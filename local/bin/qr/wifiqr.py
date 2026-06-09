#!/usr/bin/env python3
import logging
import re
import subprocess
import sys

# Standard, clean logging setup
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("WiFi-QR")


def get_current_ssid(iface: str) -> str | None:
    try:
        # Running iwctl directly
        res = subprocess.run(
            ["iwctl", "station", iface, "show"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Simple, common search for the targeted line
        for line in res.stdout.splitlines():
            if "Connected network" in line:
                # Split on '=' and strip spaces/hidden characters
                return line.split("=", 1)[1].strip()
    except subprocess.CalledProcessError:
        log.error(f"Failed to query interface '{iface}'.")
    return None


def get_wifi_password(ssid: str) -> str | None:
    """Reads the passphrase directly from the standard iwd storage path."""
    try:
        # Use sudo -A to cat the network file
        res = subprocess.run(
            ["sudo", "-A", "cat", f"/var/lib/iwd/{ssid}.psk"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in res.stdout.splitlines():
            if line.startswith("Passphrase="):
                return line.split("=", 1)[1].strip()
    except subprocess.CalledProcessError:
        log.error(f"Could not read password for '{ssid}'. Check sudo settings.")
    return None


def main(iface: str = "wlan0"):
    ssid = get_current_ssid(iface)
    if not ssid:
        return
    log.info(f"Connected to SSID: {ssid}")
    password = get_wifi_password(ssid)
    # regex escaping for special characters (\ ; : , ")
    escaped_ssid = re.sub(r"([\\;:,\"])", r"\\\1", ssid)
    if password:
        escaped_pass = re.sub(r"([\\;:,\"])", r"\\\1", password)
        payload = f"WIFI:T:WPA;S:{escaped_ssid};P:{escaped_pass};;"
    else:
        log.warning("No password found. Generating open network code.")
        payload = f"WIFI:T:nopass;S:{escaped_ssid};;"
    subprocess.run(["qrencode", "-t", "ANSIUTF8", payload])


if __name__ == "__main__":
    target_interface = sys.argv[1] if len(sys.argv) > 1 else "wlan0"
    main(iface=target_interface)
