#!/usr/bin/env python3
import sys
import subprocess
import json
from pathlib import Path


class HzScroller:
    LOCAL_BIN = Path.home() / ".local" / "bin"
    CACHE_DIR = Path.home() / ".cache"
    INDEX_FILE = CACHE_DIR / "fav_index"
    COMMANDS = [
        ("󰅍", LOCAL_BIN / "clipboard" / "clippy.py", "Clipboard History\t"),
        ("󰉐", LOCAL_BIN / "folders" / "mountencrypted.sh", "Mount Encrypted Folder\t"),
        ("󱄺", LOCAL_BIN / "fav" / "ocrmenu.sh", "OCR Menu\t"),
        ("󰐳", LOCAL_BIN / "fav" / "qrmenu.sh", "QR Menu\t"),
        ("", LOCAL_BIN / "fav" / "winemenu.sh", "Wine Menu\t"),
    ]

    @classmethod
    def ensure_cache_dir(cls):
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def read_index(cls) -> int:
        cls.ensure_cache_dir()
        try:
            return int(cls.INDEX_FILE.read_text().strip())
        except Exception:
            return 0

    @classmethod
    def write_index(cls, index: int):
        cls.ensure_cache_dir()
        cls.INDEX_FILE.write_text(str(index))

    @classmethod
    def output(cls):
        index = cls.read_index()
        icon, _, desc = cls.COMMANDS[index]
        print(json.dumps({"text": icon, "tooltip": desc}))

    @classmethod
    def scroll(cls, direction: str):
        index = cls.read_index()
        if direction == "up":
            index = (index + 1) % len(cls.COMMANDS)
        elif direction == "down":
            index = (index - 1) % len(cls.COMMANDS)
        cls.write_index(index)

    @classmethod
    def exec_current(cls):
        index = cls.read_index()
        _, script, _ = cls.COMMANDS[index]
        if script.exists():
            try:
                subprocess.run([str(script)], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Execution failed: {e}")
        else:
            print(f"Script not found: {script}")

    @classmethod
    def run(cls, args):
        if not args:
            cls.output()
            return

        if args[0] in ("up", "down"):
            cls.scroll(args[0])
        elif args[0] == "exec":
            cls.exec_current()
        else:
            cls.output()


if __name__ == "__main__":
    HzScroller.run(sys.argv[1:])
