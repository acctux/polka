#!/usr/bin/env python3
import json
from pathlib import Path


def split_sender_email(sender: str) -> tuple[str, str]:
    name: str = "Unknown Sender"
    email: str = "Unknown Email"
    if not sender.strip():
        return name, email
    name, email = sender.split("<")
    email = email.strip(">")
    name = name.strip(" '\"\\")
    return name, email


def create_toolbar(emails: list[dict[str, str]], count: int, max_items: int) -> str:
    lines = [f"<b>{count} Unread Email(s):</b>\n"]
    for mail in emails[:max_items]:
        sender, email = split_sender_email(mail.get("sender", ""))
        subject = mail.get("subject", "(No Subject)")
        email_line = [
            f"<b>{sender}</b> ({email})\t",
            f"<b>Subj</b>: {subject[:40]}\t\n",
        ]
        lines.append("\n".join(email_line))
    if count > max_items:
        lines.append(f"<i>...and {count - max_items} more</i>")
    return "\t\n".join(lines)


def show_emails(
    cache_file: Path = Path.home() / ".cache" / "emailcheck" / "last_email.json",
    icon: str = "󰇮",
    max_items: int = 10,
):
    if not cache_file.exists():
        print(json.dumps({"text": ""}))
        return
    try:
        emails = json.loads(cache_file.read_text(encoding="utf-8"))
        count = len(emails)
        if count == 0:
            print(json.dumps({"text": ""}))
            return
        tooltip = create_toolbar(emails, count, max_items)
        print(json.dumps({"text": f"{icon}", "tooltip": tooltip}))
    except Exception:
        print(json.dumps({"text": ""}))


if __name__ == "__main__":
    show_emails()
