#!/usr/bin/env python3
import logging
import re
import subprocess
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="\033[34m%(levelname)s: %(message)s\033[0m",
    stream=sys.stderr,
)
log = logging.getLogger("QR")


def handle_decoded(raw_payload: str) -> None:
    # zbarimg output: 'TYPE:content' Strip prefix.
    decoded = raw_payload.split(":", 1)[1] if ":" in raw_payload else raw_payload
    decoded = decoded.strip()
    if decoded.startswith(("http://", "https://")):
        log.info(f"Opening URL: {decoded}")
        subprocess.run(["xdg-open", decoded], check=False)
    elif decoded.startswith("WIFI:"):
        log.info("WiFi configuration detected.")
        connect_wifi(decoded)
    else:
        log.info("Copying text to clipboard.")
        subprocess.run(["wl-copy"], input=decoded, text=True, check=True)


def connect_wifi(decoded: str, scan_sleep: int = 4) -> None:
    ssid_match = re.search(r"S:([^;]+);", decoded)
    pass_match = re.search(r"P:([^;]+);", decoded)
    if not ssid_match:
        log.error("Could not parse SSID from WiFi string.")
        return
    ssid = ssid_match.group(1)
    if pass_match:
        password = pass_match.group(1)
    log.info(f"Scanning for network: {ssid}...")
    cmd = ["iwctl", "station", "wlan0", "scan"]
    subprocess.run(cmd, check=False)
    time.sleep(scan_sleep)
    cmd = ["iwctl", "station", "wlan0", "connect", ssid]
    if password:
        cmd.extend(["--passphrase", password])
    log.info(f"Connecting to {ssid} via iwd...")
    subprocess.run(cmd, check=False)


def main():
    slurp = subprocess.run(["slurp"], capture_output=True, text=True, check=False)
    if slurp.returncode != 0 or not slurp.stdout.strip():
        log.info("Selection cancelled.")
        return
    region = slurp.stdout.strip()
    log.info("Capturing and scanning region...")
    cmd = ["grim", "-g", region, "-"]
    grim = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    cmd = ["zbarimg", "--quiet", "-"]
    zbar = subprocess.Popen(cmd, stdin=grim.stdout, stdout=subprocess.PIPE, text=True)
    if grim.stdout:
        grim.stdout.close()
    stdout, _ = zbar.communicate()
    if zbar.returncode == 0 and stdout:
        handle_decoded(stdout.strip())
    elif zbar.returncode == 4:
        log.warning("No QR code found in selected region.")
    else:
        log.error("Failed to process image or run scanning tools.")


if __name__ == "__main__":
    main()
