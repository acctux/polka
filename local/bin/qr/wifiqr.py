#!/usr/bin/env python3

import subprocess

INTERFACE = "wlan0"


def run(cmd):
    return subprocess.check_output(cmd, text=True)


def get_ssid():
    out = run(["iwctl", "station", INTERFACE, "show"])
    for line in out.splitlines():
        if "Connected network" in line:
            return line.split()[-1]


def get_psk(ssid):
    path = f"/var/lib/iwd/{ssid}.psk"
    try:
        out = subprocess.check_output(["sudo", "-A", "cat", path], text=True)
        for line in out.splitlines():
            if line.startswith("Passphrase="):
                return line.split("=", 1)[1].strip()
    except subprocess.CalledProcessError:
        return None


def show_qr(ssid, password):
    subprocess.run(
        ["qrencode", "-t", "ANSIUTF8", f"WIFI:T:WPA;S:{ssid};P:{password};;"]
    )


def main():
    ssid = get_ssid()
    if not ssid:
        print("Not connected.")
        return

    password = get_psk(ssid)
    if not password:
        print(f"No password for: {ssid}")
        return

    print(ssid)
    show_qr(ssid, password)


if __name__ == "__main__":
    main()

