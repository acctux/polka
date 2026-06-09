#!/usr/bin/env python3

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class TaskwarriorEvent:
    title: str
    target_date: date
    due_in_days: int
    status: str
    uuid: str
    urgency: float


class TaskwarriorDirectLoader:
    def __init__(self):
        self.today = date.today()
        self.db_path = (
            Path.home()
            / "Lit"
            / "Docs"
            / "secdots"
            / "config"
            / "task"
            / "taskchampion.sqlite3"
        )

    def load_active_tasks(self) -> list[TaskwarriorEvent]:
        if not self.db_path.exists():
            return []

        # Connect directly to TaskChampion's operational key-value DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Taskwarrior 3 structures tasks in a flat key-value operation table
            cursor.execute("SELECT uuid, key, value FROM task_attributes")
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            # Fallback if your build named the table 'tasks' instead of 'task_attributes'
            try:
                cursor.execute("SELECT uuid, key, value FROM tasks")
                rows = cursor.fetchall()
            except sqlite3.OperationalError:
                return []
        finally:
            conn.close()

        # Group flat database rows into isolated multi-attribute entities
        task_maps = {}
        for uuid, key, value in rows:
            if uuid not in task_maps:
                task_maps[uuid] = {}
            task_maps[uuid][key] = value

        events = []
        for uuid, attrs in task_maps.items():
            status = attrs.get("status")

            # Filter criteria: ignore templates and ensure a timeline limit exists
            if status == "recurring" or "due" not in attrs:
                continue

            try:
                # Taskwarrior 3 values are Unix Epoch strings; transform directly to int
                due_timestamp = int(attrs["due"])
                target_date = date.fromtimestamp(due_timestamp)
            except (ValueError, TypeError):
                continue

            # Read floating-point metrics safely
            try:
                urgency = float(attrs.get("urgency", 0.0))
            except ValueError:
                urgency = 0.0

            events.append(
                TaskwarriorEvent(
                    title=attrs.get("description", "Untitled Task"),
                    target_date=target_date,
                    due_in_days=(target_date - self.today).days,
                    status=status or "unknown",
                    uuid=uuid,
                    urgency=urgency,
                )
            )

        return events
