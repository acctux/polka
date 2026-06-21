#!/usr/bin/env python3
import json
from pathlib import Path


def create_tooltip(emails: list[dict[str, str]], count: int, max_items: int) -> str:
    lines = [f"<b>{count} Unread Email(s):</b>\n"]
    for mail in emails[:max_items]:
        sender = mail.get("sender", "")
        name, email = sender.split("<")
        email = email.strip(">")
        name = name.strip(" '\"\\")
        subject = mail.get("subject", "No Subject")
        email_line = f"<b>{name}</b> {email}\t\n{subject[:40]}\t\n"
        lines.append(email_line)
    if count > max_items:
        lines.append(f"<i>...and {count - max_items} more</i>")
    return "\t\n".join(lines)


def show_emails(icon: str = "󰇮", max_items: int = 10):
    cache_file: Path = Path.home() / ".cache" / "emailcheck" / "last_email.json"
    emails = json.loads(cache_file.read_text(encoding="utf-8"))
    count = len(emails)
    if count == 0 or not cache_file.exists():
        print(json.dumps({"text": ""}))
        return
    tooltip = create_tooltip(emails, count, max_items)
    print(json.dumps({"text": f"{icon}", "tooltip": tooltip}))


if __name__ == "__main__":
    show_emails()
