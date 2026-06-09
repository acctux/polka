#!/usr/bin/env python3

import sys
import logging
import subprocess
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from pathlib import Path
import yaml


######################################
# LOG LOGIC
######################################
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.INFO: "\033[36m",
        logging.WARNING: "\033[93m",
        logging.ERROR: "\033[31m",
    }
    RESET = "\033[0m"
    NAME = "\033[93m"

    def format(self, record):
        name = f"{self.NAME}{record.name}{self.RESET}"
        msg = f"{self.COLORS.get(record.levelno, '')}{record.getMessage()}{self.RESET}"
        return f"{name}: {msg}"


def get_logger(log_name=None, level=logging.INFO):
    log = logging.getLogger(log_name)
    if log.handlers:
        return log
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(ColorFormatter())
    log.addHandler(handler)
    log.setLevel(level)
    log.propagate = False
    return log


log = get_logger("Polka")


######################################
# Event
######################################
@dataclass(frozen=True)
class Event:
    title: str
    due_in: int
    target_date: date
    schedule_date: date

    @property
    def date_str(self) -> str:
        return self.target_date.strftime("%Y-%m-%d")

    @property
    def next_week_str(self) -> str:
        return (self.target_date + timedelta(days=7)).strftime("%Y-%m-%d")


#######################################
# EventLoader
#######################################
class EventLoader:
    def __init__(self, today: date):
        self.today = today

    def load_all(
        self, yaml_conf: Path, contacts_dir: Path, default_due_in: int = 5
    ) -> list[Event]:
        events = []
        events.extend(self._load_from_yaml(yaml_conf))
        events.extend(self._load_from_vcards(contacts_dir, default_due_in))
        return events

    def _load_from_yaml(self, yaml_conf: Path) -> list[Event]:
        if not yaml_conf.exists():
            return []
        try:
            data = yaml.safe_load(yaml_conf.read_text())
        except (yaml.YAMLError, OSError):
            return []
        if not data or not isinstance(data, dict):
            return []
        events = []
        for item in data.get("weekly", []):
            if isinstance(item, dict) and "weekday" in item:
                events.append(self._parse_weekly(item))
        for item in data.get("scheduled", []):
            if isinstance(item, dict) and "date" in item:
                events.append(self._parse_scheduled(item))
        return events

    def _parse_weekly(self, item: dict) -> Event:
        title = item["name"]
        day_str = str(item["weekday"])[:3].title()
        due_in_val = item.get("due_in", 0)
        WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        idx = WEEKDAYS.index(day_str)
        days_ahead = (idx - self.today.weekday()) % 7
        target_date = self.today + timedelta(days=days_ahead)
        schedule_date = target_date - timedelta(days=due_in_val)
        due_in_days = (target_date - self.today).days
        return Event(title, due_in_days, target_date, schedule_date)

    def _parse_scheduled(self, item: dict) -> Event:
        title = item["name"]
        raw_date = str(item["date"]).strip()
        due_in_val = item.get("due_in", 0)
        if "-" in raw_date and len(raw_date.split("-")) == 2:
            try:
                target_date = date.fromisoformat(f"{self.today.year}-{raw_date}")
                if target_date < self.today:
                    target_str = f"{self.today.year + 1}-{raw_date}"
                    target_date = date.fromisoformat(target_str)
            except ValueError:
                target_date = self.today
        else:
            try:
                target_date = date.fromisoformat(raw_date)
            except ValueError:
                target_date = self.today
        schedule_date = target_date - timedelta(days=due_in_val)
        due_in = (target_date - self.today).days
        return Event(title, due_in, target_date, schedule_date)

    def _get_target_date(self, month: int, day: int) -> date:
        try:
            target_date = date(self.today.year, month, day)
            if target_date < self.today:
                target_date = date(self.today.year + 1, month, day)
            return target_date
        except ValueError:
            if month == 2 and day == 29:
                return self._get_target_date(3, 1)
            return self.today

    def _load_from_vcards(
        self,
        contacts_dir: Path,
        default_due_in=5,
    ) -> list[Event]:
        events: list[Event] = []
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
                    bday_raw = "".join(c for c in bday if c.isdigit())
                    if len(bday_raw) == 8:
                        month, day = int(bday_raw[4:6]), int(bday_raw[6:8])
                    elif len(bday_raw) == 6:
                        month, day = int(bday_raw[2:4]), int(bday_raw[4:6])
                    elif len(bday_raw) == 4:
                        month, day = int(bday_raw[:2]), int(bday_raw[2:4])
                    else:
                        continue
                    target_date = self._get_target_date(month, day)
                    schedule_date = target_date - timedelta(days=default_due_in)
                    due_in = (target_date - self.today).days
                    events.append(
                        Event(f"{name}'s Birthday", due_in, target_date, schedule_date)
                    )
                except Exception as e:
                    log.warning(f"Error parsing vCard {file.name}: {e}")
        return events


#######################################
# EventEngine
#######################################
class EventEngine:
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
            for task in tasks_data:
                name = str(task.get("description", "")).strip()
                due_date_str = _parse_tw_date(task.get("due", ""))
                task_tuples.add((name, due_date_str))
            return task_tuples
        except Exception as e:
            log.error(f"Failed to read Taskwarrior data: {e}")
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
            log.error(f"Failed to read Khal events: {e}")
            return set()

    def push_to_khal(self, title: str, date_str: str) -> None:
        log.info(f"[Sync -> Khal] Adding yearly event: {title} on {date_str}")
        cmd = ["khal", "new", date_str, title, "-r", "yearly"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def push_to_taskwarrior(self, title: str, date_str: str) -> None:
        log.info(f"[Sync -> Taskwarrior] Provisioning new task: {title} due {date_str}")
        cmd = ["task", "add", title, f"due:{date_str}"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


#######################################
# DateSyncManager
#######################################
class DateSyncManager:
    default_due_in = 5

    def __init__(self, yaml_conf: Path, contact_dir: Path, calendar: str) -> None:
        self.yaml_conf = yaml_conf
        self.contact_dir = contact_dir
        self.today: date = date.today()
        self.now_str: str = self.today.strftime("%Y-%m-%d")
        self.next_yr_str: str = (self.today + timedelta(days=365)).strftime("%Y-%m-%d")
        self.event_loader: EventLoader = EventLoader(self.today)
        self.events_engine: EventEngine = EventEngine(calendar)

    def run(self) -> None:
        log.info("Initializing system execution sync engines.")
        events = self.event_loader.load_all(
            self.yaml_conf,
            self.contact_dir,
            self.default_due_in,
        )
        for event in events:
            existing_tasks = self.events_engine.fetch_taskwarrior_tasks()
            existing_khal = self.events_engine.fetch_khal_events(
                self.now_str, self.next_yr_str
            )
            self._process_event(event, existing_tasks, existing_khal)
        log.info("Sync transaction completed successfully.\n")

    def _process_event(
        self,
        event: Event,
        existing_tasks: set[tuple[str, str]],
        existing_khal: set[tuple[str, str]],
    ) -> None:
        in_task = (event.title, event.date_str) in existing_tasks
        in_khal = (event.title, event.date_str) in existing_khal
        if in_task and in_khal:
            log.info(
                f"[Present] {event.title} -> "
                f"Scheduled Threshold Window Opened: {event.schedule_date.strftime('%Y-%m-%d')} "
                f"Due Target: {event.date_str} (Next Roll Window: {event.next_week_str})"
            )
            return
        if not in_khal:
            log.info(
                f"[Added] {event.title} -> "
                f"Scheduled Threshold Window Opened: {event.schedule_date.strftime('%Y-%m-%d')} "
                f"Due Target: {event.date_str} (Next Roll Window: {event.next_week_str})"
            )
            self.events_engine.push_to_khal(event.title, event.date_str)
        if not in_task:
            if self.today < event.schedule_date:
                log.info(
                    f"[Skipped] {event.title} -> Due Target: {event.date_str} "
                    f"(Preparation threshold opens on: {event.schedule_date.strftime('%Y-%m-%d')})"
                )
            else:
                self.events_engine.push_to_taskwarrior(event.title, event.date_str)


#######################################
# MAIN
#######################################
if __name__ == "__main__":
    YAML_PATH = Path.home() / ".local" / "bin" / "taskwarrior" / "dates.yaml"
    CONTACTS_PATH = Path.home() / "Desktop" / "Contacts"
    CALENDAR_NAME = "private"
    manager = DateSyncManager(YAML_PATH, CONTACTS_PATH, CALENDAR_NAME)
    manager.run()
