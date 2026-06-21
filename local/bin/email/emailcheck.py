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
    cmd = [
        "systemctl",
        "--user",
        "is-active",
        "--quiet",
        "protonmail-bridge.service",
    ]
    active = subprocess.run(cmd)
    if active.returncode != 0:
        cmd = ["systemctl", "--user", "start", "protonmail-bridge.service"]
        subprocess.run(cmd)
        time.sleep(60)
    cmd = [f"{Path.home()}/.local/bin/email/emailsync.sh"]
    subprocess.run(cmd, capture_output=True)
    if not neomutt_running():
        cmd = ["systemctl", "--user", "stop", "protonmail-bridge.service"]
        subprocess.run(cmd)


def get_new_emails(last_id: str, max_limit: int) -> list[tuple[str, str, str]]:
    cmd = ["notmuch", "search", f"--limit={max_limit}", "--format=json", "tag:inbox"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
    except json.JSONDecodeError:
        return []
    new_emails = []
    for item in data:
        msg_id = item.get("thread")
        if msg_id == last_id:
            break
        author = item.get("authors", "")
        subject = item.get("subject", "")
        new_emails.append((msg_id, author, subject))
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
    max_emails = 15
    new_emails = get_new_emails(last_id, max_emails)
    if last_id and len(new_emails) == max_emails:
        new_emails = []
    if new_emails:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        cache_list = []
        for id, author, subject in new_emails:
            cache_list.append({"id": id, "sender": author, "subject": subject})
        STATE_FILE.write_text(json.dumps(cache_list, indent=2))
        await notify_and_listen(new_emails)


if __name__ == "__main__":
    asyncio.run(main())
