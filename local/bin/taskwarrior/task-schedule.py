#!/usr/bin/env python3


from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import yaml
import json
import subprocess


FILE = Path(__file__).parent / "dates.yaml"


# ---------- TYPES ----------
Task = dict[str, Any]
Event = dict[str, Any]
TaskMap = dict[str, datetime]
PendingSet = set[str]


# ---------- UTIL ----------
def norm(s: str) -> str:
    return s.strip().lower()


# ---------- LOAD ----------
def load_events() -> list[Event]:
    with open(FILE, "r") as f:
        data = yaml.safe_load(f)
    return data["events"]


def get_tasks() -> list[Task]:
    return json.loads(
        subprocess.run(["task", "export"], capture_output=True, text=True).stdout
    )


def within_due_window(base: datetime, lead_days: int) -> bool:
    now = datetime.today()
    reminder_date = base - timedelta(days=lead_days)
    return now >= reminder_date


# ---------- STATE ----------
def build_state(tasks: list[Task]) -> tuple[PendingSet, TaskMap]:
    pending: PendingSet = set()
    last_done: TaskMap = {}
    for t in tasks:
        name = t.get("description")
        if not name:
            continue
        key = norm(name)
        if t.get("status") == "pending":
            pending.add(key)
        elif t.get("status") == "completed":
            end = t.get("end")
            if not end:
                continue
            dt = datetime.strptime(end, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            if key not in last_done or dt > last_done[key]:
                last_done[key] = dt
    return pending, last_done


def recently_done(key: str, last_done: TaskMap, window_days: int) -> bool:
    last = last_done.get(key)
    if not last:
        return False
    return datetime.now(timezone.utc) - last < timedelta(days=window_days)


# ---------- DATE ----------
def resolve_base_date(date: str | None) -> datetime:
    today = datetime.today()
    if not date:
        return today
    if date == today.strftime("%a"):
        return today
    if "-" in date:
        month, day = map(int, date.split("-"))
        base = datetime(today.year, month, day)
        if base < today:
            base = datetime(today.year + 1, month, day)
        return base
    return today


# ---------- TASK ----------
def add_task(name: str, due: datetime) -> None:
    subprocess.run(
        ["task", "add", name, f"due:{due:%Y-%m-%d}"],
        capture_output=True,
        text=True,
    )


# ---------- MAIN ----------
def main() -> None:
    events: list[Event] = load_events()
    tasks: list[Task] = get_tasks()
    pending, last_done = build_state(tasks)
    print(pending, last_done)
    for event in events:
        name: str = event["name"]
        key: str = norm(name)
        lead: int = int(event.get("due_days", 0))
        if key in pending:
            continue
        if recently_done(key, last_done, lead):
            continue
        event_date = event.get("date")
        base: datetime = resolve_base_date(event_date)
        if not within_due_window(base, lead):
            continue
        due: datetime = base
        print(f"+ {name} → {due.date()}")
        add_task(name, due)


if __name__ == "__main__":
    main()
