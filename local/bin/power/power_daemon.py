#!/usr/bin/env python3
from pathlib import Path
import time
import subprocess

HOME = Path.home()
ONLINE_PATH = "/sys/class/power_supply/ADP0/online"
INTERVAL = 1.5
SCRIPT_PATH = HOME / ".local/bin/power/tuned.py"


def get_ac_state(path: str) -> str:
    with open(path) as f:
        state = "battery"
        if f.read().strip() == 1:
            state = "ac"
        return state


def notify(msg: str, profile: str):
    cmd = [
        "notify-send",
        msg,
        profile,
        "-i",
        "/usr/share/icons/WhiteSur-dark/devices/scalable/battery.svg",
    ]
    subprocess.run(cmd)


def run_tuned(power_script: Path, msg: str, profile: str, hz: int):
    cmd = [str(power_script), profile, str(hz)]
    subprocess.run(cmd)
    notify(msg, f"Profile: {profile} | Refresh rate: {hz}Hz")


def main(
    online_path: str = ONLINE_PATH,
    interval: float = INTERVAL,
    power_script_path: Path = SCRIPT_PATH,
):
    last_state = get_ac_state(online_path)
    while True:
        state = get_ac_state(online_path)
        if state != last_state:
            if state == "battery":
                run_tuned(
                    power_script=power_script_path,
                    msg="On battery",
                    profile="laptop-battery-powersave",
                    hz=60,
                )
            elif state == "ac":
                run_tuned(
                    power_script=power_script_path,
                    msg="On AC",
                    profile="balanced",
                    hz=165,
                )
            last_state = state
        time.sleep(interval)


if __name__ == "__main__":
    main()
