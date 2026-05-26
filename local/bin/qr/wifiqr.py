#!/usr/bin/env python3
import subprocess


def main(iface: str):
    for line in subprocess.check_output(
        ["iwctl", "station", iface, "show"], text=True
    ).splitlines():
        if "Connected network" in line:
            ssid = line.split()[-1]
    for line in subprocess.check_output(
        ["sudo", "-A", "cat", f"/var/lib/iwd/{ssid}.psk"], text=True
    ).splitlines():
        if line.startswith("Passphrase="):
            password = line.split("=", 1)[1].strip()
    if not password:
        print(f"No password for: {ssid}")
        return
    subprocess.run(
        ["qrencode", "-t", "ANSIUTF8", f"WIFI:T:WPA;S:{ssid};P:{password};;"]
    )


if __name__ == "__main__":
    main(iface="wlan0")
