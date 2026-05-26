#!/usr/bin/env python3

import os
import subprocess
from pathlib import Path
import time
import imaplib2


HOME = Path.home()
CREDENTIAL_FILE = HOME / ".ssh/bridge_creds.txt"
LAST_EMAIL_FILE = HOME / ".cache/last_email.txt"


class ProtonMailBridgeNotifier:
    SLEEP_TIME = 20

    def __init__(self, credential_file: Path, last_email_file: Path):
        self.creds = self.load_or_prompt_credentials(credential_file)
        self.last_email_file = last_email_file
        self.last_email: tuple[str, str] = self.load_last_email(last_email_file)
        self.manage_service("start")
        time.sleep(self.SLEEP_TIME)

    def manage_service(self, action: str = "start") -> None:
        subprocess.run(["systemctl", "--user", action, "protonmail-bridge.service"])

    def load_or_prompt_credentials(self, credential_file: Path) -> tuple[str, str]:
        def prompt(title: str, text: str, hide=False) -> str:
            cmd = ["zenity", "--entry", f"--title={title}", f"--text={text}"]
            if hide:
                cmd.append("--hide-text")
            return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()

        user_mane = ""
        password = ""
        if not credential_file.exists():
            credential_file.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                "zenity",
                "--entry",
                "--title=ProtonMail",
                '--text="Enter full email: "',
            ]
            user_mane = subprocess.run(
                cmd, capture_output=True, text=True
            ).stdout.strip()
            password = prompt("ProtonMail", "Enter password:", hide=True)
            credential_file.write_text(f"USERNAME={user_mane}\nPASSWORD={password}\n")
            os.chmod(credential_file, 0o600)
        else:
            for line in credential_file.read_text().splitlines():
                if "USERNAME=" in line:
                    user_mane = line.strip().split("=", 1)[1]
                if "PASSWORD=" in line:
                    password = line.strip().split("=", 1)[1]
        return user_mane, password

    def load_last_email(self, last_email_file: Path) -> tuple[str, str]:
        if not last_email_file.exists():
            last_email_file.parent.mkdir(parents=True, exist_ok=True)
            return "", ""
        lines = last_email_file.read_text().strip().splitlines()
        return lines[0], lines[1] if len(lines) > 1 else ""

    def fetch_last_five(self, imap: imaplib2.IMAP4) -> list[tuple[str, str]]:
        try:
            _, data = imap.search(None, "ALL")
            email_ids = data[0].split()
            last_five: list[tuple[str, str]] = []
            for email_index in range(-1, -6, -1):
                _, msg_data = imap.fetch(
                    email_ids[email_index], "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM)])"
                )
                header_lines = msg_data[0][1].decode().splitlines()
                sender = header_lines[0].replace("From: ", "").strip()
                subject = header_lines[1].replace("Subject: ", "").strip()
                last_five.append((sender, subject))
            return last_five
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def check_email(self) -> None:
        def signout(imap: imaplib2.IMAP4):
            imap.close()
            imap.logout()
            self.manage_service("stop")

        imap = imaplib2.IMAP4("127.0.0.1", 1143)
        imap.login(self.creds[0], self.creds[1])
        imap.select("INBOX")
        last_five = self.fetch_last_five(imap)
        if not last_five:
            signout(imap)
            return
        new_emails: list[tuple[str, str]] = []
        for i, email in enumerate(last_five):
            if email == self.last_email:
                new_emails = last_five[:i]
        print(new_emails)
        for email in new_emails:
            sender, subject = email
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
        if last_five:
            sender, subject = last_five[0]
            self.last_email_file.write_text(f"{sender}\n{subject}")
        signout(imap)


if __name__ == "__main__":
    ProtonMailBridgeNotifier(CREDENTIAL_FILE, LAST_EMAIL_FILE).check_email()
