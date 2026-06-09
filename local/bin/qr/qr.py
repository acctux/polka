#!/usr/bin/env python3
import logging
import re
import subprocess
import sys
import time

# Configure clean, standard logging output
logging.basicConfig(
    level=logging.INFO,
    format="\033[34m%(levelname)s: %(message)s\033[0m",
    stream=sys.stderr,
)
log = logging.getLogger("QR")


def handle_decoded(raw_payload: str) -> None:
    """Parses zbarimg output formats and executes contextual system triggers."""
    # zbarimg outputs 'TYPE:content' (e.g., 'QR-Code:https://...'). Strip the prefix.
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
    """Parses credentials and attempts iwd connection."""
    ssid_match = re.search(r"S:([^;]+);", decoded)
    pass_match = re.search(r"P:([^;]+);", decoded)
    if not ssid_match:
        log.error("Could not parse SSID from WiFi string.")
        return
    ssid = ssid_match.group(1)
    password = pass_match.group(1) if pass_match else None
    log.info(f"Scanning for network: {ssid}...")
    subprocess.run(["iwctl", "station", "wlan0", "scan"], check=False)
    time.sleep(scan_sleep)
    cmd = ["iwctl", "station", "wlan0", "connect", ssid]
    if password:
        cmd.extend(["--passphrase", password])
    log.info(f"Connecting to {ssid} via iwd...")
    subprocess.run(cmd, check=False)


def main():
    # 1. Capture screen region selection via slurp
    slurp = subprocess.run(["slurp"], capture_output=True, text=True, check=False)
    if slurp.returncode != 0 or not slurp.stdout.strip():
        log.info("Selection cancelled.")
        return
    region = slurp.stdout.strip()
    # 2. Pipe grim straight to zbarimg via a UNIX pipeline. No file cache needed!
    log.info("Capturing and scanning region...")
    cmd = ["grim", "-g", region, "-"]
    grim = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    cmd = ["zbarimg", "--quiet", "-"]
    zbar = subprocess.Popen(cmd, stdin=grim.stdout, stdout=subprocess.PIPE, text=True)
    # Allow grim to receive a SIGPIPE if zbar exits early
    if grim.stdout:
        grim.stdout.close()
    stdout, _ = zbar.communicate()
    # 3. Handle outcomes based on exit code
    if zbar.returncode == 0 and stdout:
        handle_decoded(stdout.strip())
    elif zbar.returncode == 4:
        log.warning("No QR code found in selected region.")
    else:
        log.error("Failed to process image or run scanning tools.")


if __name__ == "__main__":
    main()

