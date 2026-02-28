#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime, timedelta

INTERVAL_TASKS = [
    ("pay credit card", 2, 1),
]

DATED_TASKS = [
    ("Valentines Day", [(2, 14)], 14),
    ("Doctor's Appointment", [(4, 2)], 10),
    ("Anniversary", [(2, 1)], 14),
    ("Baby's birthday", [(9, 14)], 14),
    ("Dad's birthday", [(2, 1)], 14),
    ("Larry's b-day", [(12, 1)], 3),
]


def get_lines():
    result = subprocess.run(
        ["/usr/sbin/task", "export"], capture_output=True, text=True
    )
    print("Return code:", result.returncode)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Task export failed: {result.stderr}")
    if not result.stdout.strip():
        raise RuntimeError("Task export returned empty output")
    return json.loads(result.stdout)


def parse_completed(tasks):
    tasks_list = []
    lines = get_lines()
    for task in lines:
        if task.get("status") in ["completed", "pending"]:
            created_date = task.get("entry", "")
            completed_date = task.get("end", "")
            age = task.get("urgency", 0)
            due = task.get("due", "")
            status = task.get("status", "")
            description = task.get("description", "").strip()
            task_dict = {
                "Created": created_date,
                "Completed": completed_date,
                "Age": age,
                "Due": due,
                "Status": status,
                "Description": description,
            }
            tasks_list.append(task_dict)
    return tasks_list


def make_interval_task(description: str, due_amount: int, due_unit: str):
    subprocess.run(["task", "add", description, f"due:{due_amount}{due_unit}"])


def handle_intervals(today, task_dict, interval_tasks):
    existing_descriptions = {task["Description"] for task in task_dict}
    today = datetime.today()
    for description, interval_days, due_days in interval_tasks:
        if description in existing_descriptions:
            completed_dates = [
                datetime.strptime(task["Completed"], "%Y%m%dT%H%M%SZ")
                for task in task_dict
                if task["Description"] == description and task["Completed"]
            ]
            if completed_dates:
                print(completed_dates)
                latest_completed = max(completed_dates)
                print(latest_completed)
                next_due_date = latest_completed + timedelta(days=interval_days)
                print(next_due_date)
                print(today)
                if next_due_date <= today:
                    print(f"Scheduling next occurrence of task: {description}")
                    make_interval_task(description, interval_days, "days")
            else:
                print(f"No completed task found for {description}, scheduling it.")
                make_interval_task(description, interval_days, "days")
        else:
            print(f"Task {description} not found in existing tasks, creating it.")
            make_interval_task(description, interval_days, "days")


def handle_dated_tasks(today, completed_dict, dated_tasks):
    existing_descriptions = {task["Description"] for task in task_dict}
    for description, date_tuples, due_days in dated_tasks:
        if description not in existing_descriptions:
            for month, day in date_tuples:
                task_date = today.replace(month=month, day=day)
                if task_date - timedelta(days=due_days) < today <= task_date:
                    days_til_due = task_date + timedelta(days=due_days) - today
                    make_interval_task(description, days_til_due.days, "d")


if __name__ == "__main__":
    task_dict = parse_completed(INTERVAL_TASKS)
    print(task_dict)
    today = datetime.today().date()
    handle_intervals(today, task_dict, INTERVAL_TASKS)
    handle_dated_tasks(today, task_dict, DATED_TASKS)
