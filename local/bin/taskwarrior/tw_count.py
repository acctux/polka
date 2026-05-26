#!/usr/bin/env python3
import subprocess
import json


def main():
    tasks = []
    urgent = False
    result = subprocess.run(
        ["task", "status:pending", "export"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    data = json.loads(result)
    for task in data:
        urgency = float(task.get("urgency", 0))
        tasks.append(task.get("description", ""))
        if urgency >= 7:
            urgent = True
    if not data:
        return {"text": ""}
    tooltip = f"Active: {len(tasks)}\t\n" + "\n".join(f"• {t}\t" for t in tasks)
    output = {
        "text": str(len(tasks)),
        "tooltip": tooltip,
        "class": "critical" if urgent else "",
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
