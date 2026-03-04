#!/usr/bin/env python3
import subprocess
from datetime import datetime, timedelta, date
from pathlib import Path
from pydantic.dataclasses import dataclass
import yaml

CONFIG_FILE = Path(__file__).parent / "schedconf.yaml"


@dataclass(frozen=True)
class IntervalTask:
    interval_days: int
    due_days: int


@dataclass(frozen=True)
class DatedTask:
    dates: list[tuple[int, int]]
    due_days: int


@dataclass
class Task:
    description: str
    status: str | None
    completed: datetime | None


def load_config():
    if not CONFIG_FILE.exists():
        return {}, {}
    with open(CONFIG_FILE, "r") as f:
        data = yaml.safe_load(f) or {}
    interval_tasks = {
        k: IntervalTask(**v) for k, v in data.get("interval_tasks", {}).items()
    }
    dated_tasks = {
        k: DatedTask(dates=[tuple(d) for d in v["dates"]], due_days=v["due_days"])
        for k, v in data.get("dated_tasks", {}).items()
    }
    return interval_tasks, dated_tasks


def run_task(*args):
    result = subprocess.run(["task", *args], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] task command failed: {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout


def parse_date(value):
    return datetime.strptime(value, "%Y%m%dT%H%M%SZ") if value else None


def export_tasks():
    raw = yaml.safe_load(run_task("export") or "[]")
    return [
        Task(
            t.get("description", "").strip(), t.get("status"), parse_date(t.get("end"))
        )
        for t in raw
        if t.get("status") in {"completed", "pending"}
    ]


def add_task(desc, due):
    due_str = due.strftime("%Y-%m-%d")
    print(f"[DEBUG] Adding task '{desc}' due {due_str}")
    result = subprocess.run(
        ["task", "add", desc, f"due:{due_str}"], capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"[DEBUG] Taskwarrior output: {result.stdout.strip()}")
    else:
        print(f"[ERROR] task failed: {result.stderr.strip()}")


def handle_interval_tasks(today, tasks, interval_tasks):
    for desc, cfg in interval_tasks.items():
        exists = any(
            t.description == desc
            and (t.completed is None or t.completed.date() >= today)
            for t in tasks
        )
        if exists:
            continue
        add_task(desc, today + timedelta(days=cfg.due_days))


def handle_dated_tasks(today, tasks, dated_tasks):
    for desc, cfg in dated_tasks.items():
        exists = any(
            t.description == desc
            and (t.completed is None or t.completed.date() >= today)
            for t in tasks
        )
        if exists:
            continue
        for month, day in cfg.dates:
            try:
                event = date(today.year, month, day)
            except ValueError:
                continue
            window_start = event - timedelta(days=cfg.due_days)
            if window_start <= today <= event:
                add_task(desc, event)


def main():
    interval_tasks, dated_tasks = load_config()
    today = date.today()
    tasks = export_tasks()
    handle_interval_tasks(today, tasks, interval_tasks)
    handle_dated_tasks(today, tasks, dated_tasks)


if __name__ == "__main__":
    main()
