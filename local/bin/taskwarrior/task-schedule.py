#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime, timedelta

INTERVAL_TASKS = [
    ("pay credit card", 7, 3),
]

DATED_TASKS = [
    ("Valentines Day", [(2, 1)], 14),
    ("Anniversary", [(2, 1)], 14),
    ("Baby's birthday", [(9, 1)], 14),
    ("Larry's b-day", [(12, 1)], 3),
]


def get_lines():
    result = subprocess.run("task export", capture_output=True, text=True, shell=True)
    data = json.loads(result.stdout)
    return data


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
    for description, interval_days, due_days in interval_tasks:
        if description in existing_descriptions:
            continue
        make_interval_task(description, interval_days, "days")


def handle_dated_tasks(today, completed_dict, dated_tasks):
    existing_descriptions = {task["Description"] for task in task_dict}
    for description, date_tuples, due_days in dated_tasks:
        if description not in existing_descriptions:
            for month, day in date_tuples:
                task_date = today.replace(month=month, day=day)
                if task_date < today <= task_date + timedelta(days=due_days):
                    days_til_due = task_date + timedelta(days=due_days) - today
                    make_interval_task(description, days_til_due.days, "d")


if __name__ == "__main__":
    task_dict = parse_completed(INTERVAL_TASKS)
    today = datetime.today().date()
    handle_intervals(today, task_dict, INTERVAL_TASKS)
    handle_dated_tasks(today, task_dict, DATED_TASKS)
