#!/usr/bin/env python3

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

INDEX_FILE = Path.home() / ".cache/powerscroll/power_index"
POWER_SCRIPT = Path.home() / ".local/bin/power/tuned.py"
WAYBAR_SIGNAL = 2


@dataclass(frozen=True)
class PowerState:
    profile: str
    hz: int
    icon: str


POWER_STATES = [
    PowerState("laptop-battery-powersave", 60, "󱙷"),
    PowerState("laptop-ac-powersave", 165, "󰌪"),
    PowerState("balanced", 165, "󰗑"),
    PowerState("desktop", 165, ""),
]


def load_index() -> int:
    try:
        return int(INDEX_FILE.read_text().strip()) % len(POWER_STATES)
    except (OSError, ValueError):
        return 0


def scroll_state(index: int, direction: str) -> None:
    step = 1 if direction == "up" else -1
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(str((index + step) % len(POWER_STATES)))


def get_output(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, timeout=2
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def output_waybar(index: int) -> None:
    state = POWER_STATES[index]
    active = get_output(["tuned-adm", "active"]).partition(":")[2].strip()
    refresh = ""

    for token in get_output(["hyprctl", "monitors"]).split():
        if "@" in token:
            refresh = token.split("@", 1)[1].split(".", 1)[0]
            break

    tooltip = [f"{state.icon} {state.profile} {state.hz}Hz\t"]
    if active and refresh:
        tooltip.append(f"{active} {refresh}Hz\t")

    print(
        json.dumps(
            {
                "text": state.icon,
                "tooltip": "\n".join(tooltip),
                "class": "active" if active == state.profile else "",
            },
            ensure_ascii=False,
        )
    )


def main() -> None:
    index = load_index()
    command = sys.argv[1] if len(sys.argv) > 1 else None

    if command is None:
        output_waybar(index)
    elif command in {"up", "down"}:
        scroll_state(index, command)
        subprocess.run(
            ["pkill", f"-RTMIN+{WAYBAR_SIGNAL}", "-x", "waybar"],
            check=False,
        )
    elif command == "exec" and POWER_SCRIPT.exists():
        state = POWER_STATES[index]
        subprocess.run(
            [str(POWER_SCRIPT), state.profile, str(state.hz)],
            check=True,
        )


if __name__ == "__main__":
    main()
