#!/usr/bin/env python3
import json
import sys
import subprocess
from pathlib import Path


class TLPScroller:
    CACHE_DIR = Path.home() / ".cache"
    INDEX_FILE = CACHE_DIR / "tlp_scroll_index"
    STATE_FILE = CACHE_DIR / "tlp_scroll_state"
    COMMANDS = [
        ("󰌪", ["tuned-adm", "profile", "powersave"]),
        ("", ["tuned-adm", "profile", "balanced"]),
        ("", ["tuned-adm", "profile", "latency-performance"]),
    ]

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
        # -1=indicate “no state saved yet”
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
    def exec_current(cls) -> None:
        index = cls.load_index()
        _, command = cls.COMMANDS[index]
        subprocess.run(command)
        cls.save_state(index)

    @classmethod
    def output_waybar(cls) -> None:
        index = cls.load_index()
        icon, _ = cls.COMMANDS[index]
        active_index = cls.load_state()
        waybar_class = "active" if index == active_index else "inactive"
        print(json.dumps({"text": icon, "class": waybar_class}))

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
    TLPScroller.run(sys.argv[1:])
