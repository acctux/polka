#!/usr/bin/env python3

import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import yaml

# ======================
# CONFIG & LOGGING
# ======================
FILE = Path(__file__).parent / "dates.yaml"
logging.basicConfig(
    level=logging.INFO,
    format="\033[93m%(name)s\033[0m: \033[36m%(message)s\033[0m",
    handlers=[logging.StreamHandler(sys.stderr)],
)
log = logging.getLogger("Task")


# ======================
# MODELS & SERVICE
# ======================
@dataclass(frozen=True)
class Event:
    name: str
    date: str
    due_days: int

    @property
    def key(self) -> str:
        return self.name.strip().lower()


class TaskWarrior:
    """Manages shell data streaming to and from TaskWarrior."""

    def __init__(self, now: datetime) -> None:
        self.now = now
        self.existing_tasks = self._get_existing_tasks()

    def _get_existing_tasks(self) -> dict[str, str]:
        """Maps normalized descriptions to their status if active or relevant today."""
        try:
            res = subprocess.run(
                ["task", "export"], capture_output=True, text=True, check=True
            )
            tasks = json.loads(res.stdout)
            today = self.now.strftime("%Y%m%d")

            return {
                t["description"].strip().lower(): t["status"]
                for t in tasks
                if t.get("description")
                and (
                    t.get("status") == "pending"
                    or t.get("entry", "")[:8] == today
                    or t.get("due", "")[:8] == today
                )
            }
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            log.error(f"TaskWarrior export failed: {e}")
            return {}

    def add_task(self, name: str, due: datetime) -> None:
        due_str = due.strftime("%Y-%m-%d")
        log.info(f"Adding task: {name} (due: {due_str})")
        subprocess.run(
            ["task", "add", name, f"due:{due_str}"],
            capture_output=True,
            text=True,
            check=True,
        )


# ======================
# BUSINESS LOGIC ENGINE
# ======================
class TaskSamurai:
    """Combines extraction, timeline evaluation, and job dispatch functions."""

    days_lookup = {
        "mon": 0,
        "tue": 1,
        "wed": 2,
        "thu": 3,
        "fri": 4,
        "sat": 5,
        "sun": 6,
    }

    def __init__(self, config_path: Path, tw: TaskWarrior, now: datetime):
        self.config_path = config_path
        self.tw = tw
        self.now = now
        self.weekly_events, self.yearly_events = self.load_events()

    def load_events(self) -> tuple[list[Event], list[Event]]:
        if not self.config_path.exists():
            log.error(f"Config file missing: {self.config_path}")
            return [], []
        data = yaml.safe_load(self.config_path.read_text()) or {}
        weekly = self._parse(data.get("weekly", []), "due_in")
        yearly = self._parse(data.get("scheduled", []), "days_before")
        return weekly, yearly

    def _parse(self, raw_list: list[dict[str, Any]], offset_key: str) -> list[Event]:
        events = []
        for item in raw_list:
            try:
                events.append(
                    Event(str(item["name"]), str(item["date"]), int(item[offset_key]))
                )
            except (KeyError, ValueError):
                log.warning(f"Skipping malformed entry: {item}")
        return events

    def process_weekly(self) -> None:
        for event in self.weekly_events:
            if event.key in self.tw.existing_tasks:
                log.info(f"Skipping '{event.name}' (already exists/handled today)")
                continue
            day_str = event.date.strip().lower()[:3]
            if day_str not in self.days_lookup:
                log.error(f"Invalid weekday name for '{event.name}': {event.date}")
                continue
            days_ahead = (self.days_lookup[day_str] - self.now.weekday()) % 7
            due = self.now + timedelta(days=days_ahead)
            due = due.replace(hour=0, minute=0, second=0, microsecond=0)
            self.tw.add_task(event.name, due)

    def process_yearly(self) -> None:
        for event in self.yearly_events:
            if event.key in self.tw.existing_tasks:
                log.info(f"Skipping '{event.name}' (already exists/handled today)")
                continue
            month, day = map(int, event.date.split("-"))
            target_year = self.now.year + (
                (month, day) < (self.now.month, self.now.day)
            )
            event_date = datetime(target_year, month, day, tzinfo=timezone.utc)
            schedule_date = event_date - timedelta(days=event.due_days)
            if self.now >= schedule_date:
                self.tw.add_task(event.name, schedule_date)
            else:
                log.info(
                    f"Ignored: '{event.name}', trigger window opens: {schedule_date.date()}"
                )


# ======================
# APPLICATION ENTRY
# ======================
def main() -> None:
    now = datetime.now(timezone.utc)
    tw = TaskWarrior(now)
    samurai = TaskSamurai(FILE, tw, now)
    samurai.process_weekly()
    samurai.process_yearly()


if __name__ == "__main__":
    main()
