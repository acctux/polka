#!/usr/bin/env python3
import json
import time
import subprocess
from pathlib import Path


class NotMuchNotify:
    def __init__(self, state_file: Path):
        self.state_file = state_file

    def run(self, cmd: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, check=True, capture_output=True, text=True)

    def refresh_mail(self) -> None:
        self.run(["systemctl", "--user", "start", "protonmail-bridge.service"])
        time.sleep(60)
        self.run(["mbsync", "-Va"])
        self.run(["notmuch", "new"])

    def youve_got_mail(self, emails: list[tuple[str, str, str]]) -> None:
        latest_id = emails[0][0]
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps({"id": latest_id}))
        for _, sender, subject in reversed(emails):
            cmd = ["notify-send", sender, subject, "--icon=thunderbird"]
            self.run(cmd)

    def get_msg_ids(self, max=10) -> list[tuple[str, str, str]]:
        cmd = [
            "notmuch",
            "search",
            "--output=messages",
            "--limit",
            str(max),
            "--format=json",
            "tag:inbox",
        ]
        msg_ids: list[str] = json.loads(self.run(cmd).stdout)
        last_seen = self._load_last_id()
        new_emails = []
        for msg_id in msg_ids:
            if msg_id == last_seen:
                break
            cmd = ["notmuch", "show", "--format=json", f"id:{msg_id}"]
            raw = json.loads(self.run(cmd).stdout)[0][0][0]
            try:
                headers = raw["headers"]
                sender = headers.get("From", "")
                subject = headers.get("Subject", "")
            except Exception:
                pass
            new_emails.append((msg_id, sender, subject))
        return new_emails

    def _load_last_id(self) -> str:
        if not self.state_file.exists():
            return ""
        try:
            return json.loads(self.state_file.read_text())["id"]
        except Exception:
            return ""

    def get_email(self):
        self.refresh_mail()
        new_emails = self.get_msg_ids()
        if new_emails:
            print(new_emails)
            self.youve_got_mail(new_emails)


if __name__ == "__main__":
    notifier = NotMuchNotify(state_file=Path.home() / ".cache" / "last_email.json")
    notifier.get_email()
