#!/usr/bin/env python3
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FavConf:
    icon: str
    desc: str
    script_path: Path

    @property
    def script_str(self) -> str:
        return str(self.script_path)

    @property
    def way_print(self) -> dict:
        return {
            "text": self.icon,
            "tooltip": f"{self.desc}\t",
        }


WAYBAR_SIGNAL = 9
BASE = Path.home() / ".local" / "bin"
COMMANDS = [
    FavConf(
        icon="󰅍",
        desc="Clipboard",
        script_path=BASE / "clipboard" / "clippy.py",
    ),
    FavConf(
        icon="󰚝",
        desc="Folders",
        script_path=BASE / "folders" / "foldermenu.py",
    ),
    FavConf(
        icon="󰩬",
        desc="Screenshots",
        script_path=BASE / "screenshots" / "screenshot_menu.py",
    ),
    FavConf(
        icon="󰐳",
        desc="QR",
        script_path=BASE / "qr" / "qrmenu.sh",
    ),
    FavConf(
        icon="",
        desc="Wine",
        script_path=BASE / "wine" / "winemenu.sh",
    ),
    FavConf(
        icon="󰊿",
        desc="Translate",
        script_path=BASE / "translate" / "translator.py",
    ),
]


def main():
    INDEX_FILE = Path("/dev/shm/fav_index")
    action = sys.argv[1] if len(sys.argv) > 1 else None
    len_commands = len(COMMANDS)
    try:
        idx = int(INDEX_FILE.read_text().strip()) % len_commands
    except (FileNotFoundError, ValueError):
        idx = 0
    if action in ("up", "down"):
        step = 1 if action == "up" else -1
        new_idx = (idx + step) % len_commands
        INDEX_FILE.write_text(str(new_idx))
        subprocess.run(
            ["pkill", f"-RTMIN+{WAYBAR_SIGNAL}", "waybar"],
            capture_output=True,
            check=True,
        )
    elif action == "exec":
        subprocess.Popen([COMMANDS[idx].script_str])
    else:
        print(json.dumps(COMMANDS[idx].way_print))


if __name__ == "__main__":
    main()
