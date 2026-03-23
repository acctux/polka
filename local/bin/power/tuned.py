#!/usr/bin/env python3
import sys
import subprocess
import re
from pathlib import Path

KANSHI_CONFIG = Path.home() / "Lit/polka/config/kanshi/config"


def set_hz(target_hz: str):
    """Set refresh rate in the undocked profile of the kanshi config."""
    if not KANSHI_CONFIG.exists():
        print(f"{KANSHI_CONFIG} does not exist!")
        return
    text = KANSHI_CONFIG.read_text()

    def replace_mode(match):
        return f"mode 1920x1080@{target_hz}Hz"

    def update_undocked_profile(match):
        header, body = match.group(1), match.group(2)
        if "undocked" in header:
            body = re.sub(r"mode\s+1920x1080@\d+Hz", replace_mode, body)
        return header + body

    new_text = re.sub(
        r"(profile\s+\w+\s*{)(.*?})", update_undocked_profile, text, flags=re.DOTALL
    )

    KANSHI_CONFIG.write_text(new_text)
    print(f"Set refresh rate to {target_hz}Hz in {KANSHI_CONFIG}")
    try:
        subprocess.run(["systemctl", "--user", "restart", "kanshi.service"], check=True)
        print("kanshi.service restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart kanshi.service: {e}")


def set_profile(profile: str):
    """Switch tuned profile."""
    try:
        subprocess.run(["tuned-adm", "profile", profile], check=True)
        print(f"Switched tuned profile to '{profile}'")
    except subprocess.CalledProcessError as e:
        print(f"Failed to switch tuned profile: {e}")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"batmode", "default"}:
        print(f"Usage: {sys.argv[0]} {{batmode|default}}")
        sys.exit(1)

    if sys.argv[1] == "batmode":
        set_profile("powersave")
        set_hz("60")
    else:
        set_profile("balanced")
        set_hz("144")


if __name__ == "__main__":
    main()
