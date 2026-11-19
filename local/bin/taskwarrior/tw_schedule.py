#!/usr/bin/env python3

import json
import logging
import sqlite3
import subprocess
import sys
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


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.INFO: "\033[36m",
        logging.WARNING: "\033[93m",
        logging.ERROR: "\033[31m",
    }
    RESET = "\033[0m"
    NAME_COLOR = "\033[93m"

    def format(self, record: logging.LogRecord) -> str:
        name = f"{self.NAME_COLOR}{record.name}{self.RESET}"
        color = self.COLORS.get(record.levelno, "")
        message = f"{color}{record.getMessage()}{self.RESET}"
        return f"{name}: {message}"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(ColorFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


log = get_logger("Polka")


@dataclass(frozen=True)
class Event:
    title: str
    target_date: date
    schedule_date: date

    @property
    def date_str(self) -> str:
        return self.target_date.isoformat()

    @property
    def due_in(self) -> int:
        return (self.target_date - date.today()).days

    @property
    def next_week_str(self) -> str:
        return (self.target_date + timedelta(days=7)).isoformat()


def parse_due_in(item: dict[str, Any]) -> int:
    try:
        return int(item.get("due_in", 0))
    except (TypeError, ValueError):
        return 0


class EventLoader:
    def __init__(self, today: date) -> None:
        self.WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.today = today

    def load_all(
        self,
        yaml_path: Path,
        contacts_dir: Path,
        default_due_in: int = DEFAULT_DUE_IN,
    ) -> list[Event]:
        return self._load_from_yaml(yaml_path) + self._load_from_vcards(
            contacts_dir, default_due_in
        )

    def _load_from_yaml(self, yaml_path: Path) -> list[Event]:
        try:
            data = yaml.safe_load(yaml_path.read_text())
        except (OSError, yaml.YAMLError):
            return []

        if not isinstance(data, dict):
            return []

        events: list[Event] = []

        for item in data.get("weekly", []):
            if isinstance(item, dict) and "weekday" in item and "name" in item:
                event = self._parse_weekly(item)
                if event:
                    events.append(event)

        for item in data.get("scheduled", []):
            if isinstance(item, dict) and "date" in item and "name" in item:
                event = self._parse_scheduled(item)
                if event:
                    events.append(event)

        return events

    def _parse_weekly(self, item: dict[str, Any]) -> Event | None:
        weekday = str(item["weekday"])[:3].title()
        if weekday not in self.WEEKDAYS:
            log.warning(f"Invalid weekday: {item['weekday']!r}")
            return None

        target_date = self.today + timedelta(
            days=(self.WEEKDAYS.index(weekday) - self.today.weekday()) % 7
        )
        schedule_date = target_date - timedelta(days=parse_due_in(item))
        return Event(str(item["name"]), target_date, schedule_date)

    def _parse_scheduled(self, item: dict[str, Any]) -> Event:
        raw_date = str(item["date"]).strip()
        target_date = self._parse_target_date(raw_date)
        schedule_date = target_date - timedelta(days=parse_due_in(item))
        return Event(str(item["name"]), target_date, schedule_date)

    def _parse_target_date(self, raw_date: str) -> date:
        # MM-DD: use the next occurrence, including next year if already passed.
        if len(raw_date.split("-")) == 2:
            try:
                month, day = map(int, raw_date.split("-"))
                target = date(self.today.year, month, day)
                if target < self.today:
                    target = date(self.today.year + 1, month, day)
                return target
            except ValueError:
                return self.today

        try:
            return date.fromisoformat(raw_date)
        except ValueError:
            return self.today

    def _load_from_vcards(
        self,
        contacts_dir: Path,
        default_due_in: int,
    ) -> list[Event]:
        events: list[Event] = []

        for folder_name in ("family", "friends"):
            folder = contacts_dir / folder_name
            if not folder.exists():
                continue

            for path in folder.glob("*.vcf"):
                try:
                    event = self._parse_vcard(path, default_due_in)
                    if event:
                        events.append(event)
                except (OSError, ValueError) as exc:
                    log.warning(f"Error parsing vCard {path.name}: {exc}")

        return events

    def _parse_vcard(self, path: Path, due_in: int) -> Event | None:
        fields: dict[str, str] = {}

        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith(("FN:", "BDAY:")):
                key, value = line.split(":", 1)
                fields[key] = value.strip()

        name = fields.get("FN")
        birthday = fields.get("BDAY")
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

        target_date = self._next_occurrence(month, day)
        return Event(
            f"{name}'s Birthday",
            target_date,
            target_date - timedelta(days=due_in),
        )

    def _next_occurrence(self, month: int, day: int) -> date:
        try:
            target = date(self.today.year, month, day)
            if target < self.today:
                target = date(self.today.year + 1, month, day)
            return target
        except ValueError:
            # Treat a Feb 29 birthday as Mar 1 in non-leap years.
            if month == 2 and day == 29:
                return self._next_occurrence(3, 1)
            return self.today


class EventEngine:
    def __init__(self, calendar: str) -> None:
        self.calendar = calendar

    @staticmethod
    def _normalize_due(due: Any) -> str:
        if not due:
            return ""

        try:
            if str(due).isdigit():
                parsed = datetime.fromtimestamp(int(due))
            else:
                parsed = datetime.strptime(
                    str(due).replace("Z", ""),
                    "%Y%m%dT%H%M%S",
                )
            return parsed.strftime("%Y-%m-%d")
        except (ValueError, TypeError, OSError, OverflowError):
            return ""

    def fetch_taskwarrior_tasks(
        self,
        db_path: Path,
    ) -> set[tuple[str, str]]:
        tasks: set[tuple[str, str]] = set()

        with sqlite3.connect(db_path) as connection:
            rows = connection.execute("SELECT data FROM tasks").fetchall()

        for (blob,) in rows:
            try:
                task = json.loads(blob)
            except (json.JSONDecodeError, TypeError):
                continue

            description = (task.get("description") or "").strip()
            if description:
                tasks.add((description, self._normalize_due(task.get("due"))))

        return tasks

    def fetch_khal_events(
        self,
        start: str,
        end: str,
    ) -> set[tuple[str, str]]:
        command = [
            "khal",
            "list",
            "-a",
            self.calendar,
            "--format",
            "{title}|{start-date}",
            start,
            end,
        ]

        try:
            result = subprocess.run(
                command,
                text=True,
                check=True,
                capture_output=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            log.error(f"Failed to read Khal events: {exc}")
            return set()

        events: set[tuple[str, str]] = set()
        for line in result.stdout.splitlines():
            if "|" in line:
                title, event_date = line.split("|", 1)
                events.add((title.strip(), event_date.strip()))

        return events

    @staticmethod
    def _run(command: list[str]) -> None:
        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            log.error(f"Command failed ({command[0]}): {exc}")

    def push_to_khal(self, title: str, date_str: str) -> None:
        log.info(f"[Sync -> Khal] Adding event: {title} on {date_str}")
        self._run(["khal", "new", date_str, title])

    def push_to_taskwarrior(self, title: str, date_str: str) -> None:
        log.info(f"[Sync -> Taskwarrior] Adding task: {title} due {date_str}")
        self._run(["task", "add", title, f"due:{date_str}"])


class DateSyncManager:
    def __init__(
        self,
        yaml_path: Path,
        contacts_dir: Path,
        calendar: str,
        db_path: Path = DB_PATH,
        today: date | None = None,
    ) -> None:
        self.yaml_path = yaml_path
        self.contacts_dir = contacts_dir
        self.db_path = db_path
        self.today = today or date.today()
        self.engine = EventEngine(calendar)
        self.loader = EventLoader(self.today)

    def run(self) -> None:
        log.info("Initializing sync.")

        events = self.loader.load_all(
            self.yaml_path,
            self.contacts_dir,
            DEFAULT_DUE_IN,
        )
        task_entries = self.engine.fetch_taskwarrior_tasks(self.db_path)
        khal_entries = self.engine.fetch_khal_events(
            self.today.isoformat(),
            (self.today + timedelta(days=365)).isoformat(),
        )

        for event in events:
            self._process_event(event, task_entries, khal_entries)

        log.info("Sync completed.")

    def _process_event(
        self,
        event: Event,
        task_entries: set[tuple[str, str]],
        khal_entries: set[tuple[str, str]],
    ) -> None:
        key = (event.title, event.date_str)
        in_task = key in task_entries
        in_khal = key in khal_entries

        if in_task and in_khal:
            log.info(f"[Present] {event.title} -> Due: {event.date_str}")
            return

        if not in_khal:
            log.info(f"[Added] {event.title} -> Calendar date: {event.date_str}")
            self.engine.push_to_khal(event.title, event.date_str)
            khal_entries.add(key)

        if not in_task:
            if self.today < event.schedule_date:
                log.info(
                    f"[Skipped] {event.title} -> Due: {event.date_str}; "
                    f"preparation opens: {event.schedule_date.isoformat()}"
                )
            else:
                self.engine.push_to_taskwarrior(event.title, event.date_str)
                task_entries.add(key)


if __name__ == "__main__":
    DateSyncManager(YAML_PATH, CONTACTS_PATH, CALENDAR_NAME).run()
