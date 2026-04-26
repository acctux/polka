#!/usr/bin/env python3
import subprocess

IFACE = "wlan0"


def run(cmd):
    return subprocess.check_output(cmd, text=True)


def get_ssid():
    for line in run(["iwctl", "station", IFACE, "show"]).splitlines():
        if "Connected network" in line:
            return line.split()[-1]
    return None


def get_psk(ssid):
    try:
        out = run(["sudo", "-A", "cat", f"/var/lib/iwd/{ssid}.psk"])
        for line in out.splitlines():
            if line.startswith("Passphrase="):
                return line.split("=", 1)[1].strip()
    except subprocess.CalledProcessError:
        pass
    return None


def main():
    ssid = get_ssid()
    password = get_psk(ssid)
    if not password:
        print(f"No password for: {ssid}")
        return

    print(ssid)
    subprocess.run(
        ["qrencode", "-t", "ANSIUTF8", f"WIFI:T:WPA;S:{ssid};P:{password};;"]
    )


if __name__ == "__main__":
    main()

