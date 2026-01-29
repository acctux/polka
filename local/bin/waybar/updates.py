#!/usr/bin/env python3
import subprocess
import json
import os
import time

KEYWORDS = ["linux-", "python-", "nvidia-", "fuse", "systemd"]
MAX_TOOLTIP_LINES = 24
THRESHOLD = 10
THRESHOLD_YELLOW = 20
THRESHOLD_RED = 50


def check_lock_files():
    pacman_lock = "/var/lib/pacman/db.lck"
    checkup_lock = f"{os.getenv('TMPDIR', '/tmp')}/checkup-db-{os.getuid()}/db.lck"
    while os.path.exists(pacman_lock) or os.path.exists(checkup_lock):
        time.sleep(1)


def get_updates():
    try:
        output = subprocess.check_output(
            ["checkupdates"], text=True, stderr=subprocess.DEVNULL
        )
        return [line.split()[0] for line in output.splitlines()]
    except subprocess.CalledProcessError:
        return []


def generate_tooltip(packages, max_lines, keywords):
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


def get_css_class(updates):
    css_class = ""
    if updates > THRESHOLD_YELLOW:
        css_class = "yellow"
    if updates > THRESHOLD_RED:
        css_class = "red"
    return css_class


def main():
    check_lock_files()
    packages = get_updates()
    updates = len(packages)
    if updates < THRESHOLD:
        print(
            json.dumps(
                {
                    "text": "",
                }
            )
        )
        return
    css_class = get_css_class(updates)
    tooltip = generate_tooltip(packages, MAX_TOOLTIP_LINES, KEYWORDS)
    print(
        json.dumps(
            {
                "text": str(updates),
                "alt": str(updates),
                "tooltip": tooltip or "Click to update your system",
                "class": css_class,
            }
        )
    )


if __name__ == "__main__":
    main()
