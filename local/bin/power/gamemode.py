#!/usr/bin/env python3

import sys
import subprocess

SERVICES = ["kdeconnectd", "swaync", "waybar", "awww-daemon", "hypridle"]


def manage_services(gamemode_action: str, services: list[str] = SERVICES) -> None:
    action_map = {
        "start": "stop",
        "stop": "start",
    }
    systemd_action = action_map[gamemode_action]
    for service in services:
        cmd = ["systemctl", "--user", systemd_action, service]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Service '{service}' has been {systemd_action}ed.")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["start", "stop"]:
        print("Usage: ./script.py [start|stop]")
        sys.exit(1)
    manage_services(sys.argv[1])

