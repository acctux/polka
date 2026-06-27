#!/usr/bin/env python3
import asyncio
import json
import subprocess
import os
import time
from pathlib import Path
from dbus_fast import Variant
from dbus_fast.aio import MessageBus
from dbus_fast.constants import MessageType
from dbus_fast.message import Message


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def neomutt_running() -> bool:
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                with open(os.path.join("/proc", pid, "comm"), "r") as f:
                    process_name = f.read().strip()
                    if process_name == "neomutt":
                        return True
            except Exception:
                continue
    return False


def refresh_mail() -> None:
    check_cmd = ["systemctl", "--user", "is-active", "--quiet", "protonmail-bridge"]
    try:
        run(check_cmd)
    except subprocess.CalledProcessError:
        # If it raises an error (exit code 3), the service is NOT running.
        start_cmd = ["systemctl", "--user", "start", "protonmail-bridge.service"]
        run(start_cmd)
        time.sleep(60)
    cmd = ["mbsync", "-Va"]
    run(cmd)
    time.sleep(1)
    cmd = ["notmuch", "new"]
    run(cmd)


def get_msg_ids(last_id: str, max_email: int) -> list[tuple[str, str, str]]:
    cmd = [
        "notmuch",
        "search",
        "--output=messages",
        "--limit",
        str(max_email),
        "--format=json",
        "tag:inbox tag:unread",
    ]
    msg_ids: list[str] = json.loads(run(cmd).stdout)
    new_emails = []
    for msg_id in msg_ids:
        if msg_id == last_id:
            break
        cmd = ["notmuch", "show", "--format=json", f"id:{msg_id}"]
        raw = json.loads(run(cmd).stdout)[0][0][0]["headers"]
        try:
            sender = raw.get("From", "")
            subject = raw.get("Subject", "")
        except Exception:
            pass
        new_emails.append((msg_id, sender, subject))
    return new_emails


async def notify_and_listen(new_emails: list[tuple[str, str, str]]) -> None:
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
    sent_ids = set()
    loop_control = asyncio.get_running_loop().create_future()

    def match_signal(msg: Message) -> None:
        if (
            loop_control.done()
            or msg.message_type != MessageType.SIGNAL
            or not msg.body
            or msg.body[0] not in sent_ids
        ):
            return
        msg_id = msg.body[0]
        if msg.member == "ActionInvoked" and msg.body[1] == "default":
            subprocess.Popen(["kitty", "neomutt"])
            loop_control.set_result(True)
        elif msg.member == "NotificationClosed":
            sent_ids.discard(msg_id)
            if not sent_ids:
                loop_control.set_result(False)

    bus.add_message_handler(match_signal)
    hints = {"urgency": Variant("y", 1)}
    actions = ["default", ""]
    for _, sender, subject in reversed(new_emails):
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
                    actions,
                    hints,
                    -1,
                ],
            )
        )
        if reply.body:
            sent_ids.add(reply.body[0])
    try:
        await asyncio.wait_for(loop_control, timeout=30.0)
    except asyncio.TimeoutError:
        pass
    finally:
        try:
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
        except Exception:
            pass
        bus.disconnect()


async def main() -> None:
    STATE_FILE = Path.home() / ".cache" / "emailcheck" / "last_email.json"
    refresh_mail()
    try:
        last_id = json.loads(STATE_FILE.read_text())[0].get("id", "")
    except Exception:
        last_id = ""
    new_emails = get_msg_ids(last_id, max_email=15)
    if new_emails:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        cache_list = []
        for id, author, subject in new_emails:
            cache_list.append({"id": id, "sender": author, "subject": subject})
        STATE_FILE.write_text(json.dumps(cache_list, indent=2))
        await notify_and_listen(new_emails)


if __name__ == "__main__":
    asyncio.run(main())
