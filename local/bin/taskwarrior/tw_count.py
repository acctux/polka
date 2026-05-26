#!/usr/bin/env python3
import subprocess
import json


def main():
    result = subprocess.run(
        ["task", "status:pending", "export"], capture_output=True, text=True
    ).stdout
    data = json.loads(result)
    if not data:
        print(json.dumps({"text": ""}))
        return
    urgent = False
    tasks = []
    for task in data:
        urgency: float = task.get("urgency")
        tasks.append(task.get("description"))
        if urgency >= 7:
            urgent = True
    sum_tasks = str(len(tasks))
    tooltip = f"Active: {sum_tasks}\t\n" + "\n".join(f"• {t}\t" for t in tasks)
    output = {
        "text": sum_tasks,
        "tooltip": tooltip,
        "class": "critical" if urgent else "",
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
