#!/usr/bin/env python3
import time
import subprocess
import logging
from pathlib import Path
import sys

CACHE_FILE = Path.home() / ".cache/zbar_region.png"


def get_logger():
    logger = logging.getLogger("QR")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


log = get_logger()


def capture_region(cache) -> str | None:
    region = run_cmd(["slurp"]).stdout.strip()
    if region:
        subprocess.run(["grim", "-g", region, str(cache)], check=True)


def parse_qr(cache) -> tuple[str, str]:
    ssid = password = ""
    for item in (
        run_cmd(["zbarimg", "--quiet", str(cache)])
        .stdout.strip()
        .removeprefix("WIFI:")
        .strip(";")
    ).split(";"):
        if ":" in item:
            key, value = item.split(":", 1)
            if key == "S":
                ssid = value
            elif key == "P":
                password = value
    return ssid, password


def run_cmd(cmd):
    try:
        return subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        log.error(f"Failed : {e.stderr.strip()}")


def connect_wifi_iwd(ssid: str, password: str = "", scan_sleep: int = 4):
    run_cmd(["iwctl", "station", "wlan0", "scan"])
    time.sleep(scan_sleep)
    cmd = ["iwctl", "station", "wlan0", "connect", ssid]
    if password:
        cmd.extend(["--passphrase", password])
    run_cmd(cmd)
    log.info(f"Connected to {ssid} via iwd")


def main():
    capture_region(CACHE_FILE)
    ssid, password = parse_qr(CACHE_FILE)
    if ssid:
        connect_wifi_iwd(ssid, password)
        if CACHE_FILE.exists():
            try:
                CACHE_FILE.unlink()
                log.info("Cache file cleaned up.")
            except Exception as e:
                log.error(f"Error cleaning up: {e}")


if __name__ == "__main__":
    main()

