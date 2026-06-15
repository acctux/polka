#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
import sys

# ---------------- CONFIG ----------------
INDEX_FILE = Path.home() / ".cache" / "powerscroll" / "power_index"
POWER_SCRIPT = Path.home() / "Lit" / "polka" / "local" / "bin" / "power" / "tuned.py"


@dataclass(frozen=True)
class PowerState:
    profile: str
    hz: int
    icon: str


POWER_STATES: list[PowerState] = [
    PowerState(
        profile="laptop-battery-powersave",
        hz=60,
        icon="󱙷",
    ),
    PowerState(
        profile="laptop-ac-powersave",
        hz=165,
        icon="󰌪",
    ),
    PowerState(
        profile="balanced",
        hz=165,
        icon="󰗑",
    ),
    PowerState(
        profile="desktop",
        hz=165,
        icon="",
    ),
]


def load_index(index_file: Path) -> int:
    try:
        return int(index_file.read_text())
    except Exception:
        return 0


def active_profile() -> str | None:
    try:
        cmd = ["tuned-adm", "active"]
        out = subprocess.check_output(cmd, text=True).strip()
        return out.split(":", 1)[1].strip()
    except Exception:
        return None


def refresh_rate() -> str | None:
    try:
        cmd = ["hyprctl", "monitors"]
        out = subprocess.check_output(cmd, text=True)
        for part in out.split():
            if "@" in part:
                return part.split("@")[1].split(".")[0]
    except Exception:
        return None


# ---------------- Actions ----------------
def scroll(index_file: Path, index: int, direction: str) -> None:
    delta = 1 if direction == "up" else -1
    new_i = (index + (delta)) % len(POWER_STATES)
    index_file.parent.mkdir(parents=True, exist_ok=True)
    index_file.write_text(str(new_i))


def exec_current(state: PowerState, power_script: Path) -> None:
    if not power_script.exists():
        return
    cmd = [str(power_script), state.profile, str(state.hz)]
    subprocess.run(cmd, check=True)


# ---------------- Output ----------------
def output(power_states: list[PowerState], index: int) -> None:
    state = power_states[index]
    klass = ""
    cmd = ["tuned-adm", "active"]
    out_str = subprocess.check_output(cmd, text=True).strip()
    active = out_str.split(":", 1)[1].strip()
    refresh = refresh_rate()
    if active == state.profile:
        klass = "active"
    tooltip = [f"{state.icon} {state.profile} {state.hz}Hz\t"]
    if active and refresh:
        tooltip.append(f"{active} {refresh}Hz\t")
    waybar_dict = {
        "text": state.icon,
        "tooltip": "\n".join(tooltip),
        "class": klass,
    }
    print(json.dumps(waybar_dict, ensure_ascii=False))


# ---------------- Main ----------------
def main():
    selected_index = load_index(INDEX_FILE)
    if len(sys.argv) == 1:
        output(POWER_STATES, selected_index)
        return
    cmd = sys.argv[1]
    if cmd == "up":
        scroll(INDEX_FILE, selected_index, "up")
    elif cmd == "down":
        scroll(INDEX_FILE, selected_index, "down")
    elif cmd == "exec":
        selected_state = POWER_STATES[selected_index]
        exec_current(selected_state, POWER_SCRIPT)


if __name__ == "__main__":
    main()
