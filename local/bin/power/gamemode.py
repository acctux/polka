#!/usr/bin/env python3
import subprocess
from pathlib import Path

SERVICES = ["kdeconnectd", "swaync", "waybar", "awww-daemon", "hypridle"]
HYPRLAND_CONF = Path.home() / ".config/hypr/gamemode/init.conf"
ORIGINAL_TEXT = """\
source = ~/.config/hypr/gamemode/default.conf
"""
GAMEMODE_TEXT = """\
source = ~/.config/hypr/gamemode/gamemode.conf
"""


def stop_user_services(services):
    for svc in services:
        try:
            subprocess.run(["systemctl", "--user", "stop", svc], check=False)
            print(f"Stopped: {svc}")
        except Exception as e:
            print(f"Could not stop {svc}: {e}")
    print("User services stopped.")


def start_user_services(services):
    for svc in services:
        try:
            subprocess.run(["systemctl", "--user", "start", svc], check=False)
            print(f"Started: {svc}")
        except Exception as e:
            print(f"Could not start {svc}: {e}")
    print("User services started.")


def toggle_hyprland_conf():
    current = HYPRLAND_CONF.read_text()
    if current.strip() == ORIGINAL_TEXT.strip():
        HYPRLAND_CONF.write_text(GAMEMODE_TEXT)
        print("Switched to gamemode config.")
        stop_user_services(SERVICES)
    else:
        HYPRLAND_CONF.write_text(ORIGINAL_TEXT)
        print("Switched to original config.")
        start_user_services(SERVICES)


if __name__ == "__main__":
    toggle_hyprland_conf()
