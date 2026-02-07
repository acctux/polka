#!/usr/bin/env python3
import json
import subprocess


def notify(title: str, body: str, urgency: str = "normal") -> None:
    subprocess.run(["notify-send", f"--urgency={urgency}", title, body])


def export_tasks() -> list[dict]:
    result = subprocess.run(
        ["task", "export"],
        capture_output=True,
        text=True,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        notify("Task Reminder", "Error parsing task export", urgency="critical")
        raise


def get_pending_tasks(data: list[dict]) -> tuple[list[tuple[str, float]], bool]:
    tasks = []
    urgent = False
    for task in data:
        if task.get("status") != "pending":
            continue
        description = task.get("description", "")
        urgency = float(task.get("urgency", 0))
        tasks.append((description, urgency))
        if urgency >= 9:
            urgent = True
    tasks.sort(key=lambda x: x[1], reverse=True)
    return tasks, urgent


def build_message(tasks: list[tuple[str, float]]) -> str:
    if not tasks:
        return "You have no pending tasks."
    return "\n".join(f"• {desc}" for desc, _ in tasks)


def main() -> None:
    try:
        data = export_tasks()
    except json.JSONDecodeError:
        return
    tasks, urgent = get_pending_tasks(data)
    body = build_message(tasks)
    urgency_flag = "critical" if urgent else "normal"
    notify("To-Do Reminder", body, urgency=urgency_flag)


if __name__ == "__main__":
    main()
