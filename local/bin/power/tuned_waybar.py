#!/usr/bin/env python3
import json
import sys
import subprocess
from pathlib import Path
import re


class HzScroller:
    CACHE_DIR = Path.home() / ".cache"
    INDEX_FILE = CACHE_DIR / "hz_scroll_index"
    STATE_FILE = CACHE_DIR / "hz_scroll_state"
    COMMANDS = [
        ("󰌪", "60Hz", "batmode"),
        ("", "144Hz", "default"),
    ]

    TLP_SCRIPT = Path.home() / "Lit/polka/local/bin/power/tuned.py"

    @classmethod
    def ensure_cache_dir(cls):
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def read_int_file(cls, path: Path, default: int = 0) -> int:
        try:
            return int(path.read_text().strip())
        except Exception:
            return default

    @classmethod
    def write_int_file(cls, path: Path, value: int) -> None:
        path.write_text(str(value))

    @classmethod
    def load_index(cls) -> int:
        cls.ensure_cache_dir()
        return cls.read_int_file(cls.INDEX_FILE, default=0)

    @classmethod
    def save_index(cls, index: int) -> None:
        cls.ensure_cache_dir()
        cls.write_int_file(cls.INDEX_FILE, index)

    @classmethod
    def load_state(cls) -> int:
        cls.ensure_cache_dir()
        return cls.read_int_file(cls.STATE_FILE, default=-1)

    @classmethod
    def save_state(cls, index: int) -> None:
        cls.ensure_cache_dir()
        cls.write_int_file(cls.STATE_FILE, index)

    @classmethod
    def scroll(cls, direction: str) -> None:
        index = cls.load_index()
        if direction == "up":
            index = (index + 1) % len(cls.COMMANDS)
        elif direction == "down":
            index = (index - 1) % len(cls.COMMANDS)
        cls.save_index(index)

    @classmethod
    def output_waybar(cls) -> None:
        index = cls.load_index()
        icon, label, _ = cls.COMMANDS[index]
        active_index = cls.load_state()
        waybar_class = "active" if index == active_index else "inactive"

        # get actual Hz from hyprctl
        try:
            output = subprocess.check_output(["hyprctl", "monitors"], text=True)
            match = re.search(r"@(\d+)\.", output)
            tooltip = f"{match.group(1)}Hz" if match else "unknown"
        except Exception:
            tooltip = "unknown"

        print(json.dumps({"text": icon, "tooltip": tooltip, "class": waybar_class}))

    @classmethod
    def exec_current(cls) -> None:
        index = cls.load_index()
        _, _, mode = cls.COMMANDS[index]
        if cls.TLP_SCRIPT.exists():
            try:
                subprocess.run([str(cls.TLP_SCRIPT), mode], check=True)
                cls.save_state(index)
            except subprocess.CalledProcessError as e:
                print(f"Failed to execute {cls.TLP_SCRIPT}: {e}")

    @classmethod
    def run(cls, args) -> None:
        for arg in args:
            if arg in ("up", "down"):
                cls.scroll(arg)
                return
            elif arg == "exec":
                cls.exec_current()
                return
        cls.output_waybar()


if __name__ == "__main__":
    HzScroller.run(sys.argv[1:])

