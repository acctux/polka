#!/usr/bin/env python3
import os
import json
import subprocess
from pathlib import Path
import time
import imaplib2
from email import message_from_bytes


HOME = Path.home()
CREDENTIAL_FILE = HOME / ".ssh/bridge_creds.json"
STATE_FILE = HOME / ".cache/last_email.json"


class ProtonMailBridgeNotifier:
    SLEEP_TIME = 20
    IMAP_HOST = "127.0.0.1"
    IMAP_PORT = 1143

    def __init__(self, credential_file: Path, state_file: Path):
        self.creds = self.load_or_prompt_credentials(credential_file)
        self.state_file = state_file
        self.last_uid = self.load_last_uid(state_file)
        self.manage_service("start")
        time.sleep(self.SLEEP_TIME)

    def manage_service(self, action: str) -> None:
        subprocess.run(["systemctl", "--user", action, "protonmail-bridge.service"])

    def load_or_prompt_credentials(self, path: Path) -> tuple[str, str]:
        def prompt(title: str, text: str, hide=False) -> str:
            cmd = ["zenity", "--entry", f"--title={title}", f"--text={text}"]
            if hide:
                cmd.append("--hide-text")
            return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()

        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            data = json.loads(path.read_text())
            return data.get("username", ""), data.get("password", "")
        username = prompt("ProtonMail", "Enter full email:")
        password = prompt("ProtonMail", "Enter password:", hide=True)
        path.write_text(
            json.dumps({"username": username, "password": password}, indent=2)
        )
        os.chmod(path, 0o600)
        return username, password

    def load_last_uid(self, path: Path) -> str:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            return ""
        return json.loads(path.read_text()).get("uid", "")

    def connect(self) -> imaplib2.IMAP4:
        imap = imaplib2.IMAP4(self.IMAP_HOST, self.IMAP_PORT)
        imap.login(self.creds[0], self.creds[1])
        imap.select("INBOX")
        return imap

    def fetch_last_five(self, imap: imaplib2.IMAP4) -> list[tuple[str, str, str]]:
        try:
            _, data = imap.search(None, "ALL")
            ids = data[0].split()
            results = []
            for email_id in ids[-1:-6:-1]:
                _, uid_data = imap.fetch(email_id, "(UID)")
                uid = uid_data[0].decode().split("UID ")[1].split(")")[0]
                _, msg_data = imap.fetch(
                    email_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])"
                )
                msg = message_from_bytes(msg_data[0][1])
                sender = msg.get("From", "").strip()
                subject = msg.get("Subject", "").strip()
                results.append((uid, sender, subject))
            return results
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def get_new_emails(
        self, last_five: list[tuple[str, str, str]]
    ) -> list[tuple[str, str, str]]:
        for i, (uid, _, _) in enumerate(last_five):
            if uid == self.last_uid:
                new = last_five[:i]
                break
        else:
            new = last_five
        return new

    def notify(self, sender: str, subject: str) -> None:
        subprocess.run(
            [
                "notify-send",
                sender,
                subject,
                "--icon=thunderbird",
                "-h",
                "string:action-clicked:thunderbird",
            ]
        )

    def save_last_uid(self, uid: str) -> None:
        self.state_file.write_text(json.dumps({"uid": uid}, indent=2))

    def check_email(self) -> None:
        imap = self.connect()
        try:
            last_five = self.fetch_last_five(imap)
            if not last_five:
                return
            new_emails = self.get_new_emails(last_five)
            for _, sender, subject in reversed(new_emails):
                self.notify(sender, subject)
            self.save_last_uid(last_five[0][0])
        finally:
            imap.close()
            imap.logout()
            self.manage_service("stop")


if __name__ == "__main__":
    ProtonMailBridgeNotifier(CREDENTIAL_FILE, STATE_FILE).check_email()
