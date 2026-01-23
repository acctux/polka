#!/usr/bin/env python3
import os
import subprocess
import time
from pathlib import Path
import imaplib2

HOME = Path.home()
CREDENTIAL_FILE = HOME / ".ssh" / "bridge_creds.txt"
LAST_EMAIL_FILE = Path.home() / ".cache" / "last_email.txt"
SLEEP_TIME = 30


def zenity_prompt(title, text, hide=False):
    cmd = ["zenity", "--entry", f"--title={title}", f"--text={text}"]
    if hide:
        cmd.append("--hide-text")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("User cancelled credential entry")
    return result.stdout.strip()


def create_credentials_file():
    CREDENTIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    creds = {
        "USERNAME": zenity_prompt("ProtonMail Bridge", "Enter full email:"),
        "PASSWORD": zenity_prompt("ProtonMail Bridge", "Enter password:", hide=True),
    }
    with open(CREDENTIAL_FILE, "w") as f:
        f.write(f"USERNAME={creds['USERNAME']}\nPASSWORD={creds['PASSWORD']}\n")
    os.chmod(CREDENTIAL_FILE, 0o600)


def load_credentials():
    with open(CREDENTIAL_FILE, "r") as f:
        creds = dict(line.strip().split("=", 1) for line in f if "=" in line)
    if not all(k in creds for k in ["USERNAME", "PASSWORD"]):
        raise ValueError("Missing credentials")
    return creds


def read_last_email():
    try:
        with open(LAST_EMAIL_FILE, "r") as f:
            return f.read().strip().split("\n", 1)
    except FileNotFoundError:
        return "", ""


def write_last_email(sender, subject):
    LAST_EMAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LAST_EMAIL_FILE, "w") as f:
        f.write(f"{sender}\n{subject}")


def fetch_last_email_subject(username, password):
    try:
        imap = imaplib2.IMAP4("127.0.0.1", 1143)
        imap.login(username, password)
        imap.select("INBOX")
        _, data = imap.search(None, "ALL")
        email_ids = data[0].split()
        if not email_ids:
            return "", ""
        _, msg_data = imap.fetch(email_ids[-1], "(BODY[HEADER.FIELDS (SUBJECT FROM)])")
        header_text = msg_data[0][1].decode()
        sender = next(
            (
                line[len("From:") :].strip()
                for line in header_text.splitlines()
                if line.startswith("From:")
            ),
            "",
        )
        subject = next(
            (
                line[len("Subject:") :].strip()
                for line in header_text.splitlines()
                if line.startswith("Subject:")
            ),
            "",
        )
        return imap, sender, subject
    except imaplib2.IMAP4.error as e:
        print(f"IMAP error: {e}")
        return "", "", ""
    except Exception as e:
        print(f"Error: {e}")
        return "", "", ""


def main():
    if not CREDENTIAL_FILE.exists():
        create_credentials_file()
    creds = load_credentials()
    old_sender, old_subject = read_last_email()
    subprocess.run(["systemctl", "--user", "start", "protonmail-bridge.service"])
    time.sleep(SLEEP_TIME)
    imap, sender, subject = fetch_last_email_subject(
        creds["USERNAME"], creds["PASSWORD"]
    )
    if sender != old_sender or subject != old_subject:
        subprocess.run(["notify-send", sender, subject, "--icon=thunderbird"])
        write_last_email(sender, subject)
    imap.close()
    imap.logout()
    subprocess.run(["systemctl", "--user", "stop", "protonmail-bridge.service"])


if __name__ == "__main__":
    main()
