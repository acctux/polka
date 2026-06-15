#!/usr/bin/env python3
import json
import time
import subprocess
from pathlib import Path


state_file = Path.home() / ".cache" / "emailcheck" / "last_email.json"


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def refresh_mail() -> None:
    check_cmd = [
        "systemctl",
        "--user",
        "is-active",
        "--quiet",
        "protonmail-bridge.service",
    ]
    if not run(check_cmd).returncode == 0:
        start_cmd = ["systemctl", "--user", "start", "protonmail-bridge.service"]
        run(start_cmd)
        time.sleep(60)
    cmd = ["mbsync", "-Va"]
    run(cmd)
    time.sleep(1)
    cmd = ["notmuch", "new"]
    run(cmd)


def youve_got_mail(new_emails: list[tuple[str, str, str]]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    email_data = []
    for email_id, sender, subject in new_emails:
        email_dict = {"id": email_id, "sender": sender, "subject": subject}
        email_data.append(email_dict)
    state_file.write_text(json.dumps(email_data, indent=2))
    for _, sender, subject in reversed(new_emails):
        cmd = ["notify-send", sender, subject, "--icon=thunderbird"]
        run(cmd)


def _load_last_id() -> str:
    if not state_file.exists():
        return ""
    try:
        data = json.loads(state_file.read_text())
        if isinstance(data, list) and len(data) > 0:
            return data[0].get("id", "")
        return ""
    except Exception:
        return ""


def get_msg_ids(max=10) -> list[tuple[str, str, str]]:
    cmd = [
        "notmuch",
        "search",
        "--output=messages",
        "--limit",
        str(max),
        "--format=json",
        "tag:inbox",
    ]
    msg_ids: list[str] = json.loads(run(cmd).stdout)
    last_seen = _load_last_id()
    new_emails = []
    for msg_id in msg_ids:
        if msg_id == last_seen:
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


if __name__ == "__main__":
    refresh_mail()
    new_emails = get_msg_ids()
    if new_emails:
        print(new_emails)
        youve_got_mail(new_emails)
