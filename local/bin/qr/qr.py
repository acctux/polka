#!/usr/bin/env python3
import subprocess
import time
import logging
from pathlib import Path
import sys
import re


def get_logger():
    logger = logging.getLogger("QR")
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("\033[34m%(levelname)s: %(message)s\033[0m")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger


log = get_logger()
CACHE_FILE = Path.home() / ".cache/zbar_region.png"


def run_cmd(cmd, output=True, text=True, check=True, input=None):
    try:
        return subprocess.run(
            cmd,
            check=check,
            capture_output=output,
            text=text,
            input=input,
        )
    except subprocess.CalledProcessError as e:
        log.error(f"Failed: {e.stderr.strip()}")
        return None


def handle_decoded(decoded):
    if ":" in decoded:
        decoded = decoded.split(":", 1)[1]
    if decoded.startswith("https://"):
        log.info(f"Opening URL: {decoded}")
        run_cmd(["xdg-open", decoded], output=False, check=True)
    elif re.match(r"^WIFI:T:(WPA|WEP);S:(.*);P:(.*);;$", decoded):
        log.info(f"Connecting to: {decoded}")
        connect_wifi(decoded)
    else:
        log.info(f"Copying: {decoded}")
        run_cmd(["wl-copy"], input=decoded.encode(), output=False, check=True)


def connect_wifi(decoded, scan_sleep=4):
    ssid = password = ""
    for item in decoded.split(";"):
        item = item.strip()
        if ":" in item:
            key, value = item.split(":", 1)
            if key == "S":
                ssid = value.strip()
            elif key == "P":
                password = value.strip()
    log.info(f"Connecting to {ssid}")
    run_cmd(["iwctl", "station", "wlan0", "scan"], output=False, check=True)
    time.sleep(scan_sleep)
    cmd = ["iwctl", "station", "wlan0", "connect", ssid]
    if password:
        cmd.extend(["--passphrase", password])
    run_cmd(cmd, output=False, check=True)
    log.info(f"Connected to {ssid} via iwd")


def main():
    if region := run_cmd(["slurp"], output=True, text=True).stdout.strip():
        run_cmd(["grim", "-g", region, str(CACHE_FILE)], output=False, check=True)
        if decoded := run_cmd(
            ["zbarimg", "--quiet", str(CACHE_FILE)], output=True, text=True, check=True
        ):
            handle_decoded(decoded.stdout.strip())
    if CACHE_FILE.exists():
        try:
            CACHE_FILE.unlink()
            log.info("Cache cleaned.")
        except Exception as e:
            log.error(f"Error: {e}")


if __name__ == "__main__":
    main()
