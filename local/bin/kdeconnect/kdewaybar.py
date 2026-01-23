#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ICON = ""
ANDROID_MOUNT = Path.home() / "Phone" / "Internal"
DISCONNECTED = {
    "text": "",
}
CONNECTED = {
    "text": ICON,
    "tooltip": "Phone connected",
    "class": "connected",
}
MOUNTED = {
    "text": ICON,
    "tooltip": "Phone mounted",
    "class": "mounted",
}
STATE = DISCONNECTED.copy()


def is_phone_mounted():
    if not ANDROID_MOUNT.exists() or not ANDROID_MOUNT.is_dir():
        return False
    return any(p.is_dir() for p in ANDROID_MOUNT.iterdir())


def is_reachable() -> bool:
    result = subprocess.run(
        ["kdeconnect-cli", "-l"],
        capture_output=True,
        text=True,
        check=True,
    )
    if "paired and reachable" in result.stdout.lower():
        return True
    else:
        return False


def main():
    if is_reachable():
        state = CONNECTED
        if is_phone_mounted():
            state = MOUNTED
    else:
        state = DISCONNECTED
    print(json.dumps(state), flush=True)


if __name__ == "__main__":
    main()
