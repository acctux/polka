#!/usr/bin/env python3
import sys
import subprocess
import re
from pathlib import Path

KANSHI_CONFIG = Path.home() / "Lit/polka/config/kanshi/config"


def set_hz(target_hz: str):
    if not KANSHI_CONFIG.exists():
        print(f"{KANSHI_CONFIG} does not exist!")
        return
    text = KANSHI_CONFIG.read_text()

    def replace_mode(match):
        return f"mode 1920x1080@{target_hz}Hz"

    def update_undocked(match):
        header, body = match.group(1), match.group(2)
        if "undocked" in header:
            body = re.sub(r"mode\s+1920x1080@\d+Hz", replace_mode, body)
        return header + body

    new_text = re.sub(
        r"(profile\s+\w+\s*{)(.*?})", update_undocked, text, flags=re.DOTALL
    )
    KANSHI_CONFIG.write_text(new_text)
    print(f"Set refresh rate to {target_hz}Hz in {KANSHI_CONFIG}")

    try:
        subprocess.run(["systemctl", "--user", "restart", "kanshi.service"], check=True)
        print("kanshi.service restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart kanshi.service: {e}")


def set_profile(profile: str):
    try:
        subprocess.run(["tuned-adm", "profile", profile], check=True)
        print(f"Switched tuned profile to '{profile}'")
    except subprocess.CalledProcessError as e:
        print(f"Failed to switch tuned profile: {e}")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <profile> <hz>")
        sys.exit(1)
    set_profile(sys.argv[1])
    set_hz(sys.argv[2])


if __name__ == "__main__":
    main()
