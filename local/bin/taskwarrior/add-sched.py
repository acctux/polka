#!/usr/bin/env python3
import subprocess
from pathlib import Path
from pydantic.dataclasses import dataclass
import yaml


CONFIG_FILE = Path(__file__).parent / "taskconf.yaml"
FUZ_CONFIG = Path.home() / ".config/fuzzel/timemenu.ini"


@dataclass(frozen=True)
class IntervalTask:
    interval_days: int
    due_days: int


@dataclass
class DatedTask:
    dates: list[tuple[int, int]]
    due_days: int


class TaskManager:
    def __init__(self, config_file=CONFIG_FILE, fuz_config=FUZ_CONFIG):
        self.config_file = config_file
        self.fuz_config = fuz_config
        self.interval_tasks: dict[str, IntervalTask] = {}
        self.dated_tasks: dict[str, DatedTask] = {}
        self.load_config()

    @staticmethod
    def run_cmd(cmd, input_text=None):
        result = subprocess.run(cmd, input=input_text, text=True, capture_output=True)
        return result.stdout.strip() if result.returncode == 0 else None

    def prompt_entry(self, title, text):
        return self.run_cmd(["zenity", "--entry", f"--title={title}", f"--text={text}"])

    def prompt_int(self, title, text):
        value = self.prompt_entry(title, text)
        return int(value) if value and value.isdigit() else None

    def fuzzel_choice(self, options):
        choice = self.run_cmd(
            [
                "fuzzel",
                "--dmenu",
                f"--config={self.fuz_config}",
                "--x-margin=100",
                "--hide-prompt",
            ],
            "\n".join(options),
        )
        return choice if choice else None

    def load_config(self):
        if not self.config_file.exists():
            return
        with open(self.config_file, "r") as f:
            data = yaml.safe_load(f) or {}
        self.interval_tasks = {
            name: IntervalTask(**task)
            for name, task in data.get("interval_tasks", {}).items()
        }
        self.dated_tasks = {
            name: DatedTask(
                dates=[tuple(d) for d in task["dates"]], due_days=task["due_days"]
            )
            for name, task in data.get("dated_tasks", {}).items()
        }

    def save_config(self):
        data = {
            "interval_tasks": {
                name: task.__dict__ for name, task in self.interval_tasks.items()
            },
            "dated_tasks": {
                name: {
                    "dates": [list(d) for d in task.dates],
                    "due_days": task.due_days,
                }
                for name, task in self.dated_tasks.items()
            },
        }
        with open(self.config_file, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False, width=70)

    def add_interval_task(self, desc):
        interval_days = self.prompt_int("Interval Days", "Enter interval days:")
        due_days = self.prompt_int("Due Days", "Enter due days:")
        if interval_days is not None and due_days is not None:
            self.interval_tasks[desc] = IntervalTask(
                interval_days=interval_days, due_days=due_days
            )

    def add_dated_task(self, desc):
        date_str = self.prompt_entry("Event Date", "Enter date (MM-DD):")
        if not date_str or "-" not in date_str:
            return
        try:
            month, day = map(int, date_str.split("-"))
        except ValueError:
            return
        due_days = self.prompt_int("Due Days", "Enter due days:")
        if due_days is None:
            return
        task = self.dated_tasks.setdefault(desc, DatedTask(dates=[], due_days=due_days))
        task.dates.append((month, day))

    def delete_task(self):
        if not self.interval_tasks and not self.dated_tasks:
            self.run_cmd(["zenity", "--info", "--text=No tasks to delete."])
            return

        rows = []
        for name in self.interval_tasks:
            rows.extend(["Interval", name])
        for name in self.dated_tasks:
            rows.extend(["Dated", name])

        cmd = [
            "zenity",
            "--list",
            "--title=Delete Task",
            "--text=Select task to delete",
            "--column=Type",
            "--column=Task",
            "--print-column=ALL",
            "--separator=|",
            "--height=400",
            "--width=600",
        ] + rows

        choice = self.run_cmd(cmd)
        if not choice:
            return

        task_type, name = choice.split("|", 1)
        if task_type == "Interval":
            self.interval_tasks.pop(name, None)
        elif task_type == "Dated":
            self.dated_tasks.pop(name, None)

    def run(self):
        action = self.fuzzel_choice(
            ["Add Interval Task", "Add Dated Task", "Remove Scheduled Task"]
        )
        if not action:
            return
        if action == "Remove Scheduled Task":
            self.delete_task()
            self.save_config()
            return

        desc = self.prompt_entry("Task Description", "Enter task description:")
        if not desc:
            return

        if action == "Add Interval Task":
            self.add_interval_task(desc)
        elif action == "Add Dated Task":
            self.add_dated_task(desc)
        self.save_config()


if __name__ == "__main__":
    TaskManager().run()
