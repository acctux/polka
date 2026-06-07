#!/usr/bin/env python3

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import yaml

# Configurations
CONFIG_FILE = Path.home() / ".local" / "bin" / "taskwarrior" / "dates.yaml"
CONTACTS_DIR = Path.home() / "Desktop" / "Contacts"
KHALENDAR = "private"

logging.basicConfig(level=logging.INFO, format="\033[96mPolka\033[0m: %(message)s")


@dataclass(frozen=True)
class Event:
    title: str
    target_date: datetime
    due_in_days: int

    @property
    def date_str(self) -> str:
        return self.target_date.strftime("%Y-%m-%d")

    @property
    def next_week_str(self) -> str:
        return (self.target_date + timedelta(days=7)).strftime("%Y-%m-%d")

    @property
    def schedule_date(self) -> datetime:
        return self.target_date - timedelta(days=self.due_in_days)


class EventSource:
    def __init__(self, today: datetime):
        self.today = today
        self.weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def _get_target_date(self, month: int, day: int) -> datetime:
        dt = datetime(self.today.year, month, day)
        return dt if dt >= self.today else dt.replace(year=self.today.year + 1)

    def load_from_yaml(self, config_file: Path) -> list[Event]:
        if not config_file.exists():
            logging.warning(f"Configuration file missing at {config_file}")
            return []
        events: list[Event] = []
        try:
            data = yaml.safe_load(config_file.read_text()) or {}
            raw_events = data.get("weekly", []) + data.get("scheduled", [])
            for item in raw_events:
                name = item.get("name")
                if not name:
                    continue
                days_ahead = item.get("due_in", 0)
                if "weekday" in item:
                    try:
                        abreveation = item["weekday"][:3]
                        target_idx = self.weekdays.index(abreveation)
                        days_delta = (target_idx - self.today.weekday()) % 7
                        target_date = self.today + timedelta(days=days_delta)
                        events.append(Event(name, target_date, days_ahead))
                    except ValueError:
                        logging.warning(f"Invalid weekday specified: {item['weekday']}")
                elif "date" in item:
                    try:
                        month, day = map(int, item["date"].split("-"))
                        events.append(
                            Event(name, self._get_target_date(month, day), days_ahead)
                        )
                    except ValueError:
                        logging.warning(
                            f"Invalid date format in config: {item['date']}"
                        )
        except Exception as e:
            logging.error(f"Error reading YAML configuration: {e}")
        return events

    def load_from_vcards(self, contacts_dir: Path) -> list["Event"]:
        """
        Load birthdays from vCard files in 'family' and 'friends' subfolders.
        Supports BDAY formats:
          - YYYYMMDD
          - YYMMDD
          - --MMDD (yearless)
          - MMDD
          - YYYY-MM-DD
        """
        events: list["Event"] = []
        for folder_name in ("family", "friends"):
            folder = contacts_dir / folder_name
            if not folder.exists():
                continue
            for file in folder.glob("*.vcf"):
                try:
                    content = file.read_text(encoding="utf-8")
                    vcard = {}
                    for line in content.splitlines():
                        if line.startswith(("FN:", "BDAY:")):
                            key, value = line.split(":", 1)
                            vcard[key] = value.strip()
                    name = vcard.get("FN")
                    bday = vcard.get("BDAY")
                    if not (name and bday):
                        continue
                    bday_raw = ""
                    for c in bday:
                        if c.isdigit():
                            bday_raw += c
                    if len(bday_raw) == 8:  # YYYYMMDD
                        month, day = int(bday_raw[4:6]), int(bday_raw[6:8])
                    elif len(bday_raw) == 6:  # YYMMDD
                        month, day = int(bday_raw[2:4]), int(bday_raw[4:6])
                    elif len(bday_raw) == 4:  # --MMDD or MMDD
                        month, day = int(bday_raw[:2]), int(bday_raw[2:4])
                    else:
                        logging.warning(f"Unrecognized format {file.name}: {bday}")
                        continue
                    target_date = self._get_target_date(month, day)
                    events.append(Event(f"{name}'s Birthday", target_date, 5))
                except Exception as e:
                    logging.warning(f"Error parsing vCard {file.name}: {e}")
        return events


class SyncEngine:
    def __init__(self, calendar: str):
        self.calendar = calendar

    def fetch_taskwarrior_tasks(self) -> set[tuple[str, str]]:
        def _parse_tw_date(date_raw: str) -> str:
            try:
                dt = datetime.strptime(date_raw.replace("Z", ""), "%Y%m%dT%H%M%S")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                return ""

        try:
            cmd = ["task", "export"]
            res = subprocess.run(
                cmd,
                text=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            tasks_data = json.loads(res.stdout)
            task_tuples = set()
            window_start = datetime.now() - timedelta(days=7)
            for task in tasks_data:
                title = str(task.get("description", "")).strip()
                status = task.get("status")
                if not title or not status:
                    continue
                due_date_str = _parse_tw_date(task.get("due", ""))
                if status in ("pending", "recurring"):
                    task_tuples.add((title, due_date_str))
                elif status == "completed" and "end" in task:
                    end_dt_str = _parse_tw_date(task["end"])
                    if (
                        end_dt_str
                        and datetime.strptime(end_dt_str, "%Y-%m-%d") >= window_start
                    ):
                        task_tuples.add((title, due_date_str))
            return task_tuples
        except Exception as e:
            logging.error(f"Failed to read Taskwarrior data: {e}")
            return set()

    def fetch_khal_events(self, start_str: str, end_str: str) -> set[tuple[str, str]]:
        try:
            cmd = [
                "khal",
                "list",
                "-a",
                self.calendar,
                "--format",
                "{title}|{start-date}",
                start_str,
                end_str,
            ]
            res = subprocess.run(
                cmd,
                text=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            events = set()
            for line in res.stdout.splitlines():
                if "|" in line:
                    title, date_str = line.split("|", 1)
                    events.add((title.strip(), date_str.strip()))
            return events
        except Exception as e:
            logging.error(f"Failed to read Khal events: {e}")
            return set()

    def push_to_khal(self, title: str, date_str: str) -> None:
        logging.info(f"\033[36m[syncing -> khal]\033[0m {title} -> {date_str}")
        cmd = ["khal", "new", date_str, title, "-r", "yearly"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def push_to_taskwarrior(self, title: str, date_str: str) -> None:
        logging.info(f"\033[36m[syncing -> task]\033[0m {title} -> {date_str}")
        cmd = ["task", "add", title, f"due:{date_str}", "recur:annual"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class DateSyncManager:
    def __init__(self, config_file: Path, contact_dir: Path, calendar: str):
        self.config_file = config_file
        self.contact_dir = contact_dir
        self.today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.now_str = self.today.strftime("%Y-%m-%d")
        self.next_yr_str = self.today.replace(year=self.today.year + 1).strftime(
            "%Y-%m-%d"
        )
        self.source = EventSource(self.today)
        self.engine = SyncEngine(calendar)

    def run(self) -> None:
        logging.info("Initializing system sync engines.")
        existing_tasks = self.engine.fetch_taskwarrior_tasks()
        existing_khal = self.engine.fetch_khal_events(self.now_str, self.next_yr_str)
        all_events = self.source.load_from_yaml(
            self.config_file
        ) + self.source.load_from_vcards(self.contact_dir)
        for event in all_events:
            self._process_event(event, existing_tasks, existing_khal)
        logging.info("\nDone.")

    def _process_event(
        self, event: Event, existing_tasks: set, existing_khal: set
    ) -> None:
        in_task = (event.title, event.date_str) in existing_tasks
        in_khal = (event.title, event.date_str) in existing_khal
        if in_task and in_khal:
            logging.info(
                f"[Present] {event.title} -> "
                f"Last Scheduled: {event.schedule_date.strftime('%Y-%m-%d')} "
                f"Due: {event.date_str} (Next Scheduled: {event.next_week_str})"
            )
            return
        if not in_khal:
            self.engine.push_to_khal(event.title, event.date_str)
        if not in_task:
            if self.today < event.schedule_date:
                logging.info(
                    f"[Skipped] {event.title} -> Due: {event.date_str} "
                    f"(Schedules on: {event.schedule_date.strftime('%Y-%m-%d')})"
                )
            else:
                self.engine.push_to_taskwarrior(event.title, event.date_str)


if __name__ == "__main__":
    polka = DateSyncManager(CONFIG_FILE, CONTACTS_DIR, KHALENDAR)
    polka.run()
