#!/usr/bin/env python3

from pathlib import Path
import yaml
import subprocess

FUZZEL_CONFIG = Path.home() / ".config/fuzzel/waybar.ini"


class EventManager:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def load(self) -> list[dict]:
        """Loads and flattens weekly and scheduled events, marking their type."""
        if not self.file_path.exists():
            return []
        with open(self.file_path, "r") as f:
            data = yaml.safe_load(f) or {}
        flattened_events = []
        for item in data.get("weekly", []):
            flattened_events.append(
                {
                    "name": item.get("name"),
                    "date": item.get("date"),
                    "due_days": item.get("due_in"),
                    "type": "weekly",
                }
            )
        for item in data.get("scheduled", []):
            flattened_events.append(
                {
                    "name": item.get("name"),
                    "date": item.get("date"),
                    "due_days": item.get("days_before"),
                    "type": "scheduled",
                }
            )
        return flattened_events

    def save(self, events: list[dict]) -> None:
        data = {"weekly": [], "scheduled": []}
        for event in events:
            if event["type"] == "weekly":
                data["weekly"].append(
                    {
                        "name": event["name"],
                        "date": event["date"],
                        "due_in": event["due_days"],
                    }
                )
            else:
                data["scheduled"].append(
                    {
                        "name": event["name"],
                        "date": event["date"],
                        "days_before": event["due_days"],
                    }
                )
        with open(self.file_path, "w") as f:
            yaml.dump(data, f, sort_keys=False)

    def delete(self, name: str) -> None:
        """Removes an event by name and commits changes."""
        events = self.load()
        self.save([e for e in events if e["name"] != name])

    def add(self, name: str, date: str, due_days: int) -> str:
        """Appends a new event and returns its deduced category type."""
        event_type = "weekly" if len(date) == 3 and date.isalpha() else "scheduled"
        events = self.load()
        events.append(
            {"name": name, "date": date, "due_days": due_days, "type": event_type}
        )
        self.save(events)
        return event_type


class MenuUI:
    def __init__(self, fuzzel_config: Path = FUZZEL_CONFIG):
        self.fuzzel_config = fuzzel_config

    def run_fuzzel(self, options: list[str], prompt: str) -> str | None:
        if not options:
            return None
        width = max(map(len, options)) + 4
        choice = subprocess.run(
            [
                "fuzzel",
                "--dmenu",
                f"--width={width}",
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
        ).stdout.strip()
        return choice if choice else None

    def run_zenity_entry(self, field_label: str) -> str | None:
        """Prompts the user for a textual string input using Zenity."""
        return (
            subprocess.run(
                ["zenity", "--entry", "--title=New Event", f"--text={field_label}"],
                text=True,
                capture_output=True,
            ).stdout.strip()
            or None
        )

    def run_delete_picker(self, events: list[dict]) -> str | None:
        """Displays selection layout using Zenity columns and yields target name."""
        cmd = [
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
        for e in events:
            cmd += [e["name"], str(e["date"]), str(e["due_days"]), e["type"]]
        return (
            subprocess.run(cmd, text=True, capture_output=True).stdout.strip() or None
        )


class App:
    def __init__(self, data_file: Path):
        self.manager = EventManager(data_file)
        self.ui = MenuUI()

    def run(self) -> None:
        options = ["Create Event", "Delete Event", "Cancel"]
        choice = self.ui.run_fuzzel(options, "Action: ")
        if choice == "Create Event":
            name = self.ui.run_zenity_entry("Event name:")
            if not name:
                return
            date = self.ui.run_zenity_entry("Date (e.g., Sun or 02-14):")
            if not date:
                return
            due_days_str = self.ui.run_zenity_entry("Days notice / Due in days:")
            if not due_days_str:
                return
            try:
                due_days = int(due_days_str)
            except ValueError:
                print("! Error: Due days must be an integer.")
                return
            event_type = self.manager.add(name, date, due_days)
            print(f"+ created: {name} ({event_type})")
        elif choice == "Delete Event":
            events = self.manager.load()
            if not events:
                print("No events found to delete.")
                return
            selected = self.ui.run_delete_picker(events)
            if selected:
                self.manager.delete(selected)
                print(f"- deleted: {selected}")


if __name__ == "__main__":
    DATA_FILE = Path(__file__).parent / "dates.yaml"
    app = App(DATA_FILE)
    app.run()
