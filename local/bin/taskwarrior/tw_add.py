#!/usr/bin/env python3

import subprocess
from pathlib import Path
from typing import Any

import yaml

FUZZEL_CONFIG = Path.home() / ".config" / "fuzzel" / "waybar.ini"
DATA_FILE = Path(__file__).parent / "dates.yaml"
EVENT_TYPES = ("weekly", "monthly", "yearly")


class EventManager:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def load(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            return []

        data = yaml.safe_load(self.file_path.read_text()) or {}
        events = []
        for event_type in EVENT_TYPES:
            for item in data.get(event_type, []):
                events.append(
                    {
                        "name": item.get("name"),
                        "date": item.get("date"),
                        "due_in": item.get("due_in"),
                        "type": event_type,
                    }
                )

        return events

    def save(self, events: list[dict[str, Any]]) -> None:
        data = {event_type: [] for event_type in EVENT_TYPES}

        for event in events:
            data[event["type"]].append(
                {
                    "name": event["name"],
                    "date": event["date"],
                    "due_in": event["due_in"],
                }
            )

        self.file_path.write_text(yaml.safe_dump(data, sort_keys=False))

    def add(self, name: str, date_text: str, due_in: int | None) -> str:
        date_text = date_text.strip()

        if len(date_text) == 3 and date_text.isalpha():
            event_type = "weekly"
        elif date_text.isdigit() and 1 <= int(date_text) <= 31:
            event_type = "monthly"
        else:
            event_type = "yearly"

        events = self.load()
        events.append(
            {
                "name": name.strip(),
                "date": date_text,
                "due_in": due_in,
                "type": event_type,
            }
        )
        self.save(events)
        return event_type

    def delete(self, name: str) -> None:
        self.save([event for event in self.load() if event["name"] != name])


class MenuUI:
    def __init__(self, fuzzel_config: Path = FUZZEL_CONFIG):
        self.fuzzel_config = fuzzel_config

    def run_fuzzel(self, options: list[str], prompt: str) -> str | None:
        result = subprocess.run(
            [
                "fuzzel",
                "--dmenu",
                f"--width={max(map(len, options)) + 4}",
                "--config",
                str(self.fuzzel_config),
                "--lines",
                str(len(options)),
                "--anchor=top-left",
                f"--prompt={prompt}",
            ],
            input="\n".join(options),
            text=True,
            capture_output=True,
            check=False,
        )
        return result.stdout.strip() or None

    @staticmethod
    def run_zenity_entry(label: str) -> str | None:
        result = subprocess.run(
            ["zenity", "--entry", "--title=New Event", f"--text={label}"],
            text=True,
            capture_output=True,
            check=False,
        )
        return result.stdout.strip() or None

    @staticmethod
    def run_delete_picker(events: list[dict[str, Any]]) -> str | None:
        command = [
            "zenity",
            "--list",
            "--title=Delete Event",
            "--text=Select event to delete",
            "--column=Name",
            "--column=Date",
            "--column=Due/Notice Days",
            "--column=Type",
            "--print-column=1",
            "--height=400",
            "--width=600",
        ]

        for event in events:
            command.extend(
                [
                    str(event["name"]),
                    str(event["date"]),
                    str(event["due_in"]),
                    event["type"],
                ]
            )

        result = subprocess.run(command, text=True, capture_output=True, check=False)
        return result.stdout.strip() or None


class App:
    def __init__(self, data_file: Path):
        self.manager = EventManager(data_file)
        self.ui = MenuUI()

    def run(self) -> None:
        choice = self.ui.run_fuzzel(
            ["Create Event", "Delete Event", "Cancel"],
            "Action: ",
        )

        if choice == "Create Recurring Event":
            self.create_event()
        elif choice == "Delete Recurring Event":
            self.delete_event()

    def create_event(self) -> None:
        name = self.ui.run_zenity_entry("Event name:")
        if not name:
            return

        date_text = self.ui.run_zenity_entry(
            "Enter Weekday e.g. Sun, Monthly date e.g. 15, or Yearly date e.g. 02-14):"
        )
        if not date_text:
            return

        due_text = self.ui.run_zenity_entry("Days notice (blank for none):")
        if due_text is None:
            return

        try:
            due_in = int(due_text) if due_text else None
        except ValueError:
            print("! Error: Days notice must be an integer or blank.")
            return

        event_type = self.manager.add(name, date_text, due_in)
        print(f"+ created: {name} ({event_type})")

    def delete_event(self) -> None:
        events = self.manager.load()
        if not events:
            print("No events found to delete.")
            return

        selected = self.ui.run_delete_picker(events)
        if selected:
            self.manager.delete(selected)
            print(f"- deleted: {selected}")


if __name__ == "__main__":
    App(DATA_FILE).run()
