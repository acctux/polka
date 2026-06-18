#!/usr/bin/env python3
import asyncio
import json
import subprocess
import sys
from dbus_fast import Variant
from dbus_fast.aio import MessageBus
from dbus_fast.constants import MessageType
from dbus_fast.message import Message


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


async def send_dbus_notification(
    title: str, body: str, icon_path: str, urgent: bool
) -> None:
    bus = await MessageBus().connect()
    # CRITICAL: Instruct the system bus daemon to pass notification signals to our socket.
    await bus.call(
        Message(
            destination="org.freedesktop.DBus",
            path="/org/freedesktop/DBus",
            interface="org.freedesktop.DBus",
            member="AddMatch",
            signature="s",
            body=["type='signal',interface='org.freedesktop.Notifications'"],
        )
    )
    urgency_level = 2 if urgent else 1
    hints = {"urgency": Variant("y", urgency_level)}
    actions = ["default", "Open Taskwarrior"]
    message = Message(
        destination="org.freedesktop.Notifications",
        path="/org/freedesktop/Notifications",
        interface="org.freedesktop.Notifications",
        member="Notify",
        signature="susssasa{sv}i",
        body=[
            "Taskwarrior Reminder",  # app_name
            0,  # replaces_id
            icon_path,  # app_icon
            title,  # summary
            body,  # body
            actions,  # actions
            hints,  # hints
            -1,  # expire_timeout
        ],
    )
    reply = await bus.call(message)
    notification_id = reply.body[0]
    loop_control = asyncio.get_running_loop().create_future()

    def match_signal(msg: Message) -> None:
        # If the future is already resolved, ignore subsequent incoming signals entirely
        if loop_control.done() or msg.message_type != MessageType.SIGNAL:
            return
        if msg.member == "ActionInvoked":
            msg_id, action_key = msg.body
            if msg_id == notification_id and action_key == "default":
                subprocess.Popen(["kitty", "taskwarrior-tui"])
                loop_control.set_result(True)
        elif msg.member == "NotificationClosed":
            msg_id, _ = msg.body
            if msg_id == notification_id:
                loop_control.set_result(False)

    bus.add_message_handler(match_signal)
    try:
        await loop_control
    finally:
        await bus.call(
            Message(
                destination="org.freedesktop.DBus",
                path="/org/freedesktop/DBus",
                interface="org.freedesktop.DBus",
                member="RemoveMatch",
                signature="s",
                body=["type='signal',interface='org.freedesktop.Notifications'"],
            )
        )
        bus.disconnect()


async def main_async() -> None:
    tasks, urgent = export_tasks()
    if not tasks:
        sys.exit(0)
    body = build_message(tasks)
    if body:
        await send_dbus_notification(
            title="To-Do Reminder",
            body=body,
            icon_path="/usr/share/icons/WhiteSur-dark/apps/scalable/com.todotxt.sleek.svg",
            urgent=urgent,
        )


if __name__ == "__main__":
    asyncio.run(main_async())
