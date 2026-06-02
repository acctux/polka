#!/usr/bin/env python3
from pathlib import Path
import time
import subprocess

HOME = Path.home()


def get_ac_state(path: str) -> str:
    with open(path) as f:
        return "ac" if f.read().strip() == "1" else "battery"


def notify(msg: str, profile: str):
    subprocess.run(
        [
            "notify-send",
            msg,
            profile,
            "-i",
            "/usr/share/icons/WhiteSur-dark/devices/scalable/battery.svg",
        ]
    )


def run_tuned(msg: str, profile: str, hz: int):
    subprocess.run([str(HOME / ".local/bin/power/tuned.py"), profile, str(hz)])
    notify(msg, f"Profile: {profile} | Refresh rate: {hz}Hz")


def main(
    path: str = "/sys/class/power_supply/ADP0/online",
    interval: float = 1.5,
):
    last_state = get_ac_state(path)
    while True:
        state = get_ac_state(path)
        if state != last_state:
            if state == "battery":
                run_tuned("On battery", "laptop-battery-powersave", 60)
            elif state == "ac":
                run_tuned("On AC", "balanced", 165)
            last_state = state
        time.sleep(interval)


if __name__ == "__main__":
    main()
