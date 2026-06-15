#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

WAYBAR_SIGNAL = 9
LOCAL_BIN = Path.home() / ".local" / "bin"
INDEX_FILE = Path.home() / ".cache" / "fav_index"
COMMANDS = [
    ("󰅍", LOCAL_BIN / "clipboard" / "clippy.py", "Clipboard\t"),
    ("󰚝", LOCAL_BIN / "folders" / "foldermenu.py", "Folders\t"),
    ("󰩬", LOCAL_BIN / "screenshots" / "screenshot_menu.py", "Screenshots\t"),
    ("󰐳", LOCAL_BIN / "qr" / "qrmenu.sh", "QR\t"),
    ("", LOCAL_BIN / "wine" / "winemenu.sh", "Wine\t"),
]


def read_index() -> int:
    try:
        return int(INDEX_FILE.read_text().strip()) % len(COMMANDS)
    except (FileNotFoundError, ValueError):
        return 0


def write_index(index: int) -> None:
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(str(index))


def refresh_waybar() -> None:
    try:
        cmd = ["pkill", f"-RTMIN+{WAYBAR_SIGNAL}", "waybar"]
        subprocess.run(cmd, check=False, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass


def handle_cycle(direction: str) -> None:
    current_index = read_index()
    step = 1 if direction == "up" else -1
    new_index = (current_index + step) % len(COMMANDS)
    write_index(new_index)
    refresh_waybar()


def handle_exec() -> None:
    _, script, _ = COMMANDS[read_index()]
    if not script.exists():
        print(f"Script not found: {script}", file=sys.stderr)
        sys.exit(1)
    try:
        subprocess.run([script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Execution failed: {e}", file=sys.stderr)
        sys.exit(e.returncode)


def handle_print() -> None:
    icon, _, desc = COMMANDS[read_index()]
    print(json.dumps({"text": icon, "tooltip": desc}))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cycle and execute favorite scripts in Waybar."
    )
    parser.add_argument(
        "action",
        choices=["up", "down", "exec", "print"],
        nargs="?",
        default="print",
        help="Action to perform (default: print Waybar JSON)",
    )
    args = parser.parse_args()
    if args.action in ("up", "down"):
        handle_cycle(args.action)
    elif args.action == "exec":
        handle_exec()
    else:
        handle_print()


if __name__ == "__main__":
    main()

