#!/usr/bin/env python3
import subprocess
import json
import os
import time
from pathlib import Path

KEYWORDS = ["linux-", "python-", "nvidia-", "fuse", "systemd"]
MAX_TOOLTIP_LINES = 24
THRESHOLD = 50
THRESHOLD_YELLOW = 75
THRESHOLD_RED = 100


def check_lock_files() -> None:
    pacman_lock = Path("/var/lib/pacman/db.lck")
    checkup_lock = Path(f"{Path.home() / 'TMPDIR' / 'checkup-db'}/{os.getuid()}/db.lck")
    while pacman_lock.exists() or checkup_lock.exists():
        time.sleep(1)


def get_updates() -> list:
    try:
        cmd = ["checkupdates"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return [line.split()[0] for line in output.splitlines()]
    except subprocess.CalledProcessError:
        return []


def generate_tooltip(packages: list, max_lines: int, keywords: list) -> str:
    tooltip_lines = []
    for pkg in packages:
        if any(kw in pkg for kw in keywords):
            continue
        if len(tooltip_lines) < max_lines:
            tooltip_lines.append(f"•{pkg}")
    remaining = len(packages) - len(tooltip_lines)
    if remaining > 0:
        tooltip_lines.append(f"+{remaining} more")
    return "\n".join(tooltip_lines)


def get_css_class(threshold_yellow: int, threshold_red: int, updates: int) -> str:
    css_class = ""
    if updates > threshold_yellow:
        css_class = "yellow"
    if updates > threshold_red:
        css_class = "red"
    return css_class


def main():
    check_lock_files()
    packages = get_updates()
    num_updates = len(packages)
    if num_updates < THRESHOLD:
        print(json.dumps({"text": ""}))
        return
    css_class = get_css_class(THRESHOLD_YELLOW, THRESHOLD_RED, num_updates)
    tooltip = generate_tooltip(packages, MAX_TOOLTIP_LINES, KEYWORDS)
    waybar_dict = {
        "text": str(num_updates),
        "alt": str(num_updates),
        "tooltip": tooltip,
        "class": css_class,
    }
    print(json.dumps(waybar_dict))


if __name__ == "__main__":
    main()
