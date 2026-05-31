#!/usr/bin/env python3
import sys
import json
import subprocess


def export_tasks() -> tuple[list[tuple[str, float]], bool]:
    result = subprocess.run(["task", "export"], capture_output=True, text=True)
    data = json.loads(result.stdout)
    tasks = []
    urgent = False
    for task in data:
        if task.get("status") != "pending":
            continue
        description = task.get("description", "")
        urgency = float(task.get("urgency", 0))
        tasks.append((description, urgency))
        if urgency >= 7:
            urgent = True
    return tasks, urgent


def build_message(tasks: list[tuple[str, float]]) -> str:
    return "\n".join(f"• {desc}" for desc, _ in tasks)


def main() -> None:
    tasks, urgent = export_tasks()
    if not tasks:
        sys.exit(0)
    body = build_message(tasks)
    if body:
        crit = "normal"
        if urgent:
            crit = "critical"
        subprocess.run(
            [
                "notify-send",
                f"--urgency={crit}",
                "-i",
                "/usr/share/icons/WhiteSur-dark/apps/scalable/com.todotxt.sleek.svg",
                "To-Do Reminder",
                body,
            ]
        )


if __name__ == "__main__":
    main()
