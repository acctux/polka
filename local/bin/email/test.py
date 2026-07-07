import json
import subprocess
from pathlib import Path

CACHE_FILE = Path("/home/nick/.cache/emailcheck/last_email.json")
ZENITY_GEOMETRY = ["--width", "800", "--height", "400"]


def run_command(cmd: list[str], check: bool = True):
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def archive_messages(msg_ids: list[str]):
    if not msg_ids:
        return
    cmd = ["notmuch", "tag", "-inbox"] + [f"id:{m}" for m in msg_ids]
    run_command(cmd)
    print(f"Archived {len(msg_ids)} messages.")


def show_email_menu(emails: list[dict]):
    """Displays a Zenity checklist and archives selected items."""
    header = ["zenity", "--list", "--checklist", "--title", "Unread Emails"]
    columns = [
        "--column",
        "Select",
        "--column",
        "ID",
        "--column",
        "Sender",
        "--column",
        "Subject",
    ]
    rows = []
    for e in emails:
        rows.extend(["FALSE", e["id"], e["sender"], e["subject"]])
    result = subprocess.run(
        header + columns + ZENITY_GEOMETRY + rows, capture_output=True, text=True
    )
    if result.returncode == 0 and result.stdout.strip():
        selected_ids = result.stdout.strip().split("|")
        archive_messages(selected_ids)


def main():
    if not CACHE_FILE.exists():
        print(f"Cache file not found at {CACHE_FILE}")
        return
    with open(CACHE_FILE, "r") as f:
        emails = json.load(f)
    if emails:
        show_email_menu(emails)
    else:
        print("No unread emails found.")


if __name__ == "__main__":
    main()
