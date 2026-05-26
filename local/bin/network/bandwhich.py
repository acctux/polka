#!/usr/bin/env python3

import subprocess
import time

apps: dict[str, tuple[str, str]] = {}  # name -> (down, up)

last_print = 0


def get_info():
    p = subprocess.run(
        ["sudo", "bandwhich", "-i", "wlan0", "-r"],
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    if not p.stdout:
        return None

    for line in p.stdout:
        line = line.strip()
        if line.startswith("process:"):
            parts = line.split()[2:]

            if not parts:
                return None

            if parts[0].strip('"') != "<UNKNOWN>":
                name = parts[0].strip('"')
                down, up = parts[3].split("/")
                return name, down, up

    return None


def capture_apps(name: str, down: str, up: str):
    # just update data, NO printing here
    apps[name] = (down, up)


def print_apps():
    print("\n--- snapshot ---")
    for app, (down, up) in apps.items():
        print(app, down, up)


while True:
    result = get_info()

    if result:
        name, down, up = result
        capture_apps(name, down, up)

    # throttle printing to every 5 seconds
    now = time.time()
    if now - last_print >= 2:
        print_apps()
        last_print = now
