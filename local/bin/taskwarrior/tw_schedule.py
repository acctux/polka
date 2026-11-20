#!/usr/bin/env python3

import json
import logging
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

HOME = Path.home()
DB_PATH = HOME / ".config" / "task" / "taskchampion.sqlite3"
YAML_PATH = HOME / ".local" / "bin" / "taskwarrior" / "dates.yaml"
CONTACTS_PATH = HOME / "Desktop" / "Contacts"
CALENDAR_NAME = "private"
DEFAULT_DUE_IN = 5

log = logging.getLogger("TW-Sync")
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")


@dataclass(frozen=True)
class Event:
    title: str
    target: date
    schedule: date

    @property
    def key(self) -> tuple[str, str]:
        return self.title, self.target.isoformat()


class EventLoader:
    def __init__(self, today: date):
        self.today = today

    def load(self) -> list[Event]:
        return self._load_yaml() + self._load_contacts()

    def _load_yaml(self) -> list[Event]:
        try:
            data = yaml.safe_load(YAML_PATH.read_text()) or {}
        except (OSError, yaml.YAMLError):
            return []

        if not isinstance(data, dict):
            return []

        events = []
        for item in data.get("weekly", []):
            if isinstance(item, dict) and item.get("name") and item.get("date"):
                event = self._weekly(item)
                if event:
                    events.append(event)

        for item in data.get("monthly", []):
            if (
                isinstance(item, dict)
                and item.get("name")
                and item.get("date") is not None
            ):
                event = self._monthly(item)
                if event:
                    events.append(event)

        for item in data.get("yearly", []):
            if isinstance(item, dict) and "name" in item and "date" in item:
                target = self._parse_date(str(item["date"]).strip())
                events.append(self._event(item, target))

        return events

    def _event(self, item: dict[str, Any], target: date) -> Event:
        days_before = item.get("due_in")
        if days_before is None:
            days_before = DEFAULT_DUE_IN

        return Event(
            title=str(item["name"]),
            target=target,
            schedule=target - timedelta(days=int(days_before)),
        )

    def _weekly(self, item: dict[str, Any]) -> Event | None:
        WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
        weekday = str(item["date"])[:3].title()
        if weekday not in WEEKDAYS:
            log.warning("Invalid weekday: %r", item["date"])
            return None

        offset = (WEEKDAYS.index(weekday) - self.today.weekday()) % 7
        return self._event(item, self.today + timedelta(days=offset))

    def _monthly(self, item: dict[str, Any]) -> Event | None:
        try:
            day = int(item["date"])
            if not 1 <= day <= 31:
                raise ValueError
        except (TypeError, ValueError):
            log.warning("Invalid monthly day: %r", item["date"])
            return None

        year, month = self.today.year, self.today.month
        target = self._month_date(year, month, day)

        if target < self.today:
            year += month == 12
            month = month % 12 + 1
            target = self._month_date(year, month, day)

        return self._event(item, target)

    @staticmethod
    def _month_date(year: int, month: int, day: int) -> date:
        next_month = date(year + (month == 12), month % 12 + 1, 1)
        last_day = (next_month - timedelta(days=1)).day
        return date(year, month, min(day, last_day))

    def _parse_date(self, raw: str) -> date:
        try:
            if len(raw.split("-")) == 2:
                month, day = map(int, raw.split("-"))
                target = date(self.today.year, month, day)
                return (
                    date(self.today.year + 1, month, day)
                    if target < self.today
                    else target
                )
            return date.fromisoformat(raw)
        except ValueError:
            log.warning("Invalid scheduled date: %r", raw)
            return self.today

    def _load_contacts(self) -> list[Event]:
        events = []
        for group in ("family", "friends"):
            for path in (CONTACTS_PATH / group).glob("*.vcf"):
                try:
                    event = self._birthday(path)
                    if event:
                        events.append(event)
                except (OSError, ValueError) as exc:
                    log.warning("Could not parse %s: %s", path.name, exc)
        return events

    def _birthday(self, path: Path) -> Event | None:
        fields = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith(("FN:", "BDAY:")):
                key, value = line.split(":", 1)
                fields[key] = value.strip()

        name, birthday = fields.get("FN"), fields.get("BDAY")
        if not name or not birthday:
            return None

        digits = "".join(char for char in birthday if char.isdigit())
        if len(digits) == 8:
            month, day = int(digits[4:6]), int(digits[6:8])
        elif len(digits) == 6:
            month, day = int(digits[2:4]), int(digits[4:6])
        elif len(digits) == 4:
            month, day = int(digits[:2]), int(digits[2:])
        else:
            return None

        target = self._next_occurrence(month, day)
        return Event(
            title=f"{name}'s Birthday",
            target=target,
            schedule=target - timedelta(days=DEFAULT_DUE_IN),
        )

    def _next_occurrence(self, month: int, day: int) -> date:
        try:
            target = date(self.today.year, month, day)
        except ValueError:
            if (month, day) != (2, 29):
                return self.today
            target = date(self.today.year, 3, 1)

        if target < self.today:
            try:
                target = date(self.today.year + 1, month, day)
            except ValueError:
                target = date(self.today.year + 1, 3, 1)

        return target


class EventSync:
    def __init__(self, today: date):
        self.today = today

    @staticmethod
    def _run(command: list[str], *, capture: bool = False) -> str:
        try:
            result = subprocess.run(
                command, check=True, text=True, capture_output=capture
            )
            return result.stdout if capture else ""
        except (OSError, subprocess.CalledProcessError) as exc:
            log.error("Command failed (%s): %s", command[0], exc)
            return ""

    @staticmethod
    def _normalize_due(value: Any) -> str:
        try:
            value = str(value)
            if value.isdigit():
                return datetime.fromtimestamp(int(value)).date().isoformat()

            return (
                datetime.strptime(value.replace("Z", ""), "%Y%m%dT%H%M%S")
                .date()
                .isoformat()
            )
        except (ValueError, TypeError, OSError, OverflowError):
            return ""

    def task_entries(self) -> set[tuple[str, str]]:
        try:
            with sqlite3.connect(DB_PATH) as db:
                rows = db.execute("SELECT data FROM tasks").fetchall()
        except sqlite3.Error as exc:
            log.error("Could not read Taskwarrior database: %s", exc)
            return set()

        entries = set()
        for (blob,) in rows:
            try:
                task = json.loads(blob)
            except (json.JSONDecodeError, TypeError):
                continue

            if task.get("status").strip() == "pending":
                title = task.get("description").strip()
                entries.add((title, self._normalize_due(task.get("due"))))

        return entries

    def khal_entries(self) -> list[tuple[str, str]]:
        output = self._run(
            [
                "khal",
                "list",
                "-a",
                CALENDAR_NAME,
                "--format",
                "{title}|{start-date}",
                self.today.isoformat(),
                (self.today + timedelta(days=365)).isoformat(),
            ],
            capture=True,
        )
        khal_events = []
        for line in output.splitlines():
            if "|" in line:
                for title, event_date in [line.split("|", 1)]:
                    khal_events.append((title.strip(), event_date.strip()))
        return khal_events

    def sync(self, events: list[Event]) -> None:
        tasks = self.task_entries()
        calendar = self.khal_entries()
        for event in events:
            if event.key not in calendar:
                log.info("Adding calendar event: %s on %s", *event.key)
                self._run(["khal", "new", event.key[1], event.title])

            if event.key in tasks:
                continue

            if self.today < event.schedule:
                log.info("Skipping task %s until %s", event.title, event.schedule)
                continue

            log.info("Adding task: %s due %s", *event.key)
            self._run(["task", "add", event.title, f"due:{event.key[1]}"])


if __name__ == "__main__":
    today = date.today()
    EventSync(today).sync(EventLoader(today).load())
