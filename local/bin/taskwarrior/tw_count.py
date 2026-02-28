#!/usr/bin/env python3
import subprocess
import json


def export_tasks():
    result = subprocess.run(
        ["task", "status:pending", "export"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def collect_pending_tasks(data):
    tasks = []
    urgent = False
    for task in data:
        desc = task.get("description", "")
        urgency = float(task.get("urgency", 0))
        tasks.append(desc)
        if urgency >= 7:
            urgent = True
    return tasks, urgent


def build_output(tasks, urgent):
    if not tasks:
        return {"text": ""}
    count = len(tasks)
    tooltip = f"Active:{count}\n" + "\n".join(f"•{t}\t" for t in tasks)
    return {
        "text": str(count),
        "tooltip": tooltip,
        "class": "critical" if urgent else "todo",
    }


def main():
    tasks, urgent = collect_pending_tasks(export_tasks())
    print(json.dumps(build_output(tasks, urgent)))


if __name__ == "__main__":
    main()
