#!/usr/bin/env python3

import asyncio
import json
import subprocess
import time
from pathlib import Path

from dbus_fast import Variant
from dbus_fast.aio import MessageBus
from dbus_fast.constants import MessageType
from dbus_fast.message import Message


WAYBAR_SIGNAL = 6
STATE_FILE = Path.home() / ".cache" / "emailcheck" / "last_email.json"
MAX_EMAILS = 15
NOTIFICATION_TIMEOUT = 30


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def refresh_mail() -> None:
    try:
        run(["systemctl", "--user", "is-active", "--quiet", "protonmail-bridge"])
    except subprocess.CalledProcessError:
        run(["systemctl", "--user", "start", "protonmail-bridge"])
        time.sleep(60)

    run(["mbsync", "-Va"])
    time.sleep(1)
    run(["notmuch", "new"])


def load_last_message_id() -> str:
    try:
        messages = json.loads(STATE_FILE.read_text())
        return messages[0].get("id", "") if messages else ""
    except (OSError, json.JSONDecodeError, AttributeError, TypeError):
        return ""


def save_unread_messages(messages: list[tuple[str, str, str]]) -> None:
    data = []
    for msg_id, sender, subject in messages:
        data.append({"id": msg_id, "sender": sender, "subject": subject})

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = STATE_FILE.with_suffix(".tmp")
    temporary_file.write_text(json.dumps(data, indent=2))
    temporary_file.replace(STATE_FILE)


def get_unread_messages(
    last_message_id: str, limit: int
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    result = run(
        [
            "notmuch",
            "search",
            "--output=messages",
            "--limit",
            str(limit),
            "--format=json",
            "tag:inbox and tag:unread",
        ]
    )
    message_ids = json.loads(result.stdout)

    unread: list[tuple[str, str, str]] = []
    new_unread: list[tuple[str, str, str]] = []
    found_last_message = False

    for message_id in message_ids:
        details = json.loads(
            run(["notmuch", "show", "--format=json", f"id:{message_id}"]).stdout
        )
        headers = details[0][0][0]["headers"]
        message = (
            message_id,
            headers.get("From", ""),
            headers.get("Subject", ""),
        )
        unread.append(message)

        if not found_last_message:
            if message_id == last_message_id:
                found_last_message = True
            else:
                new_unread.append(message)

    return new_unread, unread


async def notify_and_listen(emails: list[tuple[str, str, str]]) -> None:
    bus = await MessageBus().connect()
    match_rule = "type='signal',interface='org.freedesktop.Notifications'"

    await bus.call(
        Message(
            destination="org.freedesktop.DBus",
            path="/org/freedesktop/DBus",
            interface="org.freedesktop.DBus",
            member="AddMatch",
            signature="s",
            body=[match_rule],
        )
    )

    pending_notifications: set[int] = set()
    finished = asyncio.get_running_loop().create_future()

    def handle_signal(message: Message) -> None:
        if (
            finished.done()
            or message.message_type != MessageType.SIGNAL
            or not message.body
            or message.body[0] not in pending_notifications
        ):
            return

        notification_id = message.body[0]

        if message.member == "ActionInvoked" and len(message.body) > 1:
            if message.body[1] == "default":
                subprocess.Popen(["kitty", "neomutt"])
                finished.set_result(None)
        elif message.member == "NotificationClosed":
            pending_notifications.discard(notification_id)
            if not pending_notifications:
                finished.set_result(None)

    bus.add_message_handler(handle_signal)

    try:
        for _, sender, subject in reversed(emails):
            reply = await bus.call(
                Message(
                    destination="org.freedesktop.Notifications",
                    path="/org/freedesktop/Notifications",
                    interface="org.freedesktop.Notifications",
                    member="Notify",
                    signature="susssasa{sv}i",
                    body=[
                        "Email Check",
                        0,
                        "thunderbird",
                        sender,
                        subject,
                        ["default", ""],
                        {"urgency": Variant("y", 1)},
                        -1,
                    ],
                )
            )
            if reply.body:
                pending_notifications.add(reply.body[0])

        if not pending_notifications:
            return

        try:
            await asyncio.wait_for(finished, timeout=NOTIFICATION_TIMEOUT)
        except TimeoutError:
            pass
    finally:
        await bus.call(
            Message(
                destination="org.freedesktop.DBus",
                path="/org/freedesktop/DBus",
                interface="org.freedesktop.DBus",
                member="RemoveMatch",
                signature="s",
                body=[match_rule],
            )
        )
        bus.disconnect()


async def main() -> None:
    refresh_mail()

    new_emails, unread_emails = get_unread_messages(
        load_last_message_id(),
        limit=MAX_EMAILS,
    )
    save_unread_messages(unread_emails)

    if new_emails:
        await notify_and_listen(new_emails)


if __name__ == "__main__":
    asyncio.run(main())
    subprocess.run(
        ["pkill", f"-RTMIN+{WAYBAR_SIGNAL}", "waybar"], capture_output=True, check=False
    )
