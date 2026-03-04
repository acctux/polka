#!/usr/bin/env python3
import subprocess
from pathlib import Path
from pydantic.dataclasses import dataclass
import yaml

CONFIG_FILE = Path(__file__).parent / "schedconf.yaml"
FUZ_CONFIG = Path.home() / ".config/fuzzel/task.ini"


@dataclass(frozen=True)
class IntervalTask:
    interval_days: int
    due_days: int


@dataclass
class DatedTask:
    dates: list[tuple[int, int]]
    due_days: int


def run_cmd(cmd, input_text=None):
    result = subprocess.run(cmd, input=input_text, text=True, capture_output=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def prompt_entry(title, text):
    return run_cmd(["zenity", "--entry", f"--title={title}", f"--text={text}"])


def prompt_int(title, text):
    value = prompt_entry(title, text)
    return int(value) if value and value.isdigit() else None


def fuzzel_choice(options):
    if not FUZ_CONFIG.exists():
        return None
    choice = run_cmd(
        ["fuzzel", "--dmenu", f"--config={FUZ_CONFIG}", "--hide-prompt"],
        "\n".join(options),
    )
    return choice if choice else None


def load_config():
    if not CONFIG_FILE.exists():
        return {}, {}
    with open(CONFIG_FILE, "r") as f:
        data = yaml.safe_load(f) or {}
    interval = {
        name: IntervalTask(**task)
        for name, task in data.get("interval_tasks", {}).items()
    }
    dated = {
        name: DatedTask(
            dates=[tuple(d) for d in task["dates"]], due_days=task["due_days"]
        )
        for name, task in data.get("dated_tasks", {}).items()
    }
    return interval, dated


def save_config(interval, dated):
    data = {
        "interval_tasks": {name: task.__dict__ for name, task in interval.items()},
        "dated_tasks": {
            name: {"dates": [list(d) for d in task.dates], "due_days": task.due_days}
            for name, task in dated.items()
        },
    }
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False, width=70)


def add_interval(interval, desc):
    interval_days = prompt_int("Interval Days", "Enter interval days:")
    due_days = prompt_int("Due Days", "Enter due days:")
    if interval_days is None or due_days is None:
        return
    interval[desc] = IntervalTask(interval_days=interval_days, due_days=due_days)


def add_dated(dated, desc):
    date_str = prompt_entry("Event Date", "Enter date (MM-DD):")
    if not date_str or "-" not in date_str:
        return
    try:
        month, day = map(int, date_str.split("-"))
    except ValueError:
        return
    due_days = prompt_int("Due Days", "Enter due days:")
    if due_days is None:
        return
    task = dated.setdefault(desc, DatedTask(dates=[], due_days=due_days))
    task.dates.append((month, day))


def delete_task(interval, dated):
    if not interval and not dated:
        run_cmd(["zenity", "--info", "--text=No tasks to delete."])
        return
    cmd = (
        [
            "zenity",
            "--list",
            "--title=Delete Task",
            "--text=Select task to delete",
            "--column=Type",
            "--column=Description",
            "--height=400",
            "--width=600",
        ]
        + [
            ["Interval", f"{name} (every {t.interval_days}d, due {t.due_days}d)"]
            for name, t in interval.items()
        ]
        + [
            [
                "Dated",
                f"{name} ({', '.join(f'{m:02d}-{d:02d}' for m, d in t.dates)}, due {t.due_days}d)",
            ]
            for name, t in dated.items()
        ]
    )
    cmd = [
        item
        for sublist in cmd
        for item in (sublist if isinstance(sublist, list) else [sublist])
    ]
    choice = run_cmd(cmd)
    if not choice:
        return
    task_type, name_with_info = choice.split("|")
    name = name_with_info.split(" (")[0]
    if task_type == "Interval":
        interval.pop(name, None)
    else:
        dated.pop(name, None)


def main():
    interval, dated = load_config()
    action = fuzzel_choice(
        ["Add Interval Task", "Add Dated Task", "Remove Scheduled Task"]
    )
    if not action:
        return
    if action == "Remove Scheduled Task":
        delete_task(interval, dated)
        save_config(interval, dated)
        return
    desc = prompt_entry("Task Description", "Enter task description:")
    if not desc:
        return
    if action == "Add Interval Task":
        add_interval(interval, desc)
    elif action == "Add Dated Task":
        add_dated(dated, desc)
    save_config(interval, dated)


if __name__ == "__main__":
    main()
