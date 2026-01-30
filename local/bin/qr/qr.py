#!/usr/bin/env python3
import subprocess
import logging
from pathlib import Path
import sys
import re
import dbus


def get_logger():
    logger = logging.getLogger("QR")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


logger = get_logger()
CACHE_FILE = Path.home() / ".cache/zbar_region.png"


def capture_region():
    try:
        return subprocess.run(
            ["slurp"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        logger.error("Region capture failed.")
        return None


def take_screenshot(region):
    try:
        subprocess.run(["grim", "-g", region, str(CACHE_FILE)], check=True)
    except subprocess.CalledProcessError:
        logger.error("Screenshot capture failed.")


def decode_barcode():
    try:
        return subprocess.run(
            ["zbarimg", "--quiet", str(CACHE_FILE)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        logger.error("Decoding failed.")
        return None


def handle_decoded(decoded):
    if decoded.startswith("https://"):
        subprocess.run(["xdg-open", decoded], check=True)
        logger.info(f"Opening URL: {decoded}")
    elif re.match(r"^WIFI:T:(WPA|WEP);S:(.*);P:(.*);;$", decoded):
        connect_to_wifi(decoded)
    else:
        subprocess.run(["wl-copy"], input=decoded.encode())
        logger.info(f"Copied to clipboard: {decoded}")


def connect_to_wifi(decoded):
    match = re.match(r"^WIFI:T:(WPA|WEP);S:(.*);P:(.*);;$", decoded)
    if not match:
        logger.error("Invalid Wi-Fi QR code format.")
        return
    ssid, password = match.group(2), match.group(3)
    try:
        bus = dbus.SystemBus()
        iwd = bus.get_object("org.freedesktop.iwd", "/org/freedesktop/iwd")
        networks = iwd.GetNetworks(dbus_interface="org.freedesktop.iwd.Manager")
        network_to_connect = None
        if networks:
            for network in networks:
                network_ssid = bytes(network.get("SSID")).decode("utf-8")
                if network_ssid == ssid:
                    network_to_connect = network
                    break
        if not network_to_connect:
            logger.error(f"Network {ssid} not found.")
            return
        device = iwd.GetDevice(dbus_interface="org.freedesktop.iwd.Device")
        if device:
            device.ConnectToNetwork(
                network_to_connect,
                password,
                dbus_interface="org.freedesktop.iwd.Device",
            )
            logger.info(f"Connecting to {ssid}...")
    except dbus.DBusException as e:
        logger.error(f"DBus error while connecting to Wi-Fi: {e}")


def clean_up():
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
            logger.info("Cache file cleaned up.")
        else:
            logger.warning("Cache file not found for cleanup.")
    except Exception as e:
        logger.error(f"Error cleaning up: {e}")


def main():
    region = capture_region()
    if region:
        take_screenshot(region)
        result = decode_barcode()
        if result:
            handle_decoded(result.split(":", 1)[1] if ":" in result else result)
    clean_up()


if __name__ == "__main__":
    main()
