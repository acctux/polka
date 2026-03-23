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
        ("󰌪", "laptop-battery-powersave", "60"),
        ("", "laptop-ac-powersave", "144"),
        ("󱐋", "balanced", "144"),
    ]
    TLP_SCRIPT = Path.home() / "Lit/polka/local/bin/power/tuned.py"

    @classmethod
    def ensure_cache_dir(cls):
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def read_int_file(cls, path: Path, default: int) -> int:
        try:
            return int(path.read_text().strip())
        except Exception:
            return default

    @classmethod
    def write_int_file(cls, path: Path, value: int):
        path.write_text(str(value))

    @classmethod
    def load_index(cls) -> int:
        cls.ensure_cache_dir()
        return cls.read_int_file(cls.INDEX_FILE, 0)

    @classmethod
    def save_index(cls, index: int):
        cls.ensure_cache_dir()
        cls.write_int_file(cls.INDEX_FILE, index)

    @classmethod
    def load_state(cls) -> int:
        cls.ensure_cache_dir()
        return cls.read_int_file(cls.STATE_FILE, -1)

    @classmethod
    def save_state(cls, index: int):
        cls.ensure_cache_dir()
        cls.write_int_file(cls.STATE_FILE, index)

    @classmethod
    def scroll(cls, direction: str):
        index = cls.load_index()
        index = (
            (index + 1) % len(cls.COMMANDS)
            if direction == "up"
            else (index - 1) % len(cls.COMMANDS)
        )
        cls.save_index(index)

    @classmethod
    def output_waybar(cls):
        index = cls.load_index()
        icon, _, _ = cls.COMMANDS[index]
        active_index = cls.load_state()
        waybar_class = "active" if index == active_index else "inactive"
        tooltip = "unknown"
        try:
            output = subprocess.check_output(["hyprctl", "monitors"], text=True)
            match = re.search(r"@(\d+)\.", output)
            if match:
                tooltip = f"{match.group(1)}Hz"
        except Exception:
            pass
        print(json.dumps({"text": icon, "tooltip": tooltip, "class": waybar_class}))

    @classmethod
    def exec_current(cls):
        index = cls.load_index()
        _, mode, hz = cls.COMMANDS[index]
        if cls.TLP_SCRIPT.exists():
            try:
                subprocess.run([str(cls.TLP_SCRIPT), mode, hz], check=True)
                cls.save_state(index)
            except subprocess.CalledProcessError as e:
                print(f"Failed to execute {cls.TLP_SCRIPT}: {e}")

    @classmethod
    def run(cls, args):
        if not args:
            cls.output_waybar()
            return
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

