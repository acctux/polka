#!/usr/bin/env python3
import json
import re
import subprocess
import time
from pathlib import Path

CACHE = Path("/tmp/waybar-wifi.json")


def run(cmd):
    try:
        return subprocess.check_output(
            cmd, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return ""


def find_wifi_interface():
    for dev in Path("/sys/class/net").iterdir():
        if (dev / "wireless").exists():
            return dev.name
    return None


def parse_wifi_info(station_info):
    rssi = rx = tx = None
    rssi_match = re.search(r"signal avg:\s+(-?\d+)", station_info)
    rx_match = re.search(r"rx bytes:\s+(\d+)", station_info)
    tx_match = re.search(r"tx bytes:\s+(\d+)", station_info)
    if rssi_match:
        rssi = int(rssi_match.group(1))
    if rx_match:
        rx = int(rx_match.group(1))
    if tx_match:
        tx = int(tx_match.group(1))
    return rssi, rx, tx


def compute_signal_strength(rssi):
    strength = max(0, min(100, int((rssi + 90) / 0.55)))
    ICONS = ["󰤯", "󰤟", "󰤢", "󰤥", "󰤨"]
    icon = ICONS[min(strength // 25, 4)]
    return strength, icon


def load_previous_stats():
    if not CACHE.exists():
        return None
    try:
        return json.loads(CACHE.read_text())
    except Exception:
        return None


def save_stats(rx, tx):
    CACHE.write_text(json.dumps({"rx": rx, "tx": tx, "t": time.time()}))


def compute_speeds(prev, rx, tx):
    if not prev:
        return 0, 0
    dt = time.time() - prev.get("t", 0)
    if dt <= 0.5:
        return 0, 0
    upload_rate = (tx - prev.get("tx", 0)) / dt
    download_rate = (rx - prev.get("rx", 0)) / dt
    return upload_rate, download_rate


def get_firewalld_zone():
    output = run(["firewall-cmd", "--get-active-zones"])
    if not output:
        return "off"
    first_line = output.splitlines()[0]
    zone_name = first_line.split(None, 1)[0]
    return zone_name


def build_tooltip(iface, strength, rssi, upload, download, vpn, zone_name):
    lines = [
        f"{iface}\t\n·{strength}%\t\n·{rssi}dBm\t\n↑{upload / 1_048_576:.1f}M\t\n↓{download / 1_048_576:.1f}M\t\n{zone_name} 󱨑\t"
    ]
    if vpn:
        lines.insert(0, f"{vpn}")
    return "\n".join(lines)


def output_json(icon, tooltip, vpn_active):
    print(
        json.dumps(
            {
                "text": icon,
                "tooltip": tooltip,
                "class": "vpn" if vpn_active else "wifi",
            },
            ensure_ascii=False,
        )
    )


def main():
    vpn = run(["wg", "show", "interfaces"])
    iface = find_wifi_interface() or "wlan0"
    station_info = run(["iw", "dev", iface, "station", "dump"])
    rssi, rx_bytes, tx_bytes = parse_wifi_info(station_info)
    if rssi is None or rx_bytes is None or tx_bytes is None:
        output_json("󰤫", f"No WiFi link\n{get_firewalld_zone()}", False)
        return
    strength, icon = compute_signal_strength(rssi)
    prev = load_previous_stats()
    upload, download = compute_speeds(prev, rx_bytes, tx_bytes)
    zone_name = get_firewalld_zone()
    save_stats(rx_bytes, tx_bytes)
    tooltip = build_tooltip(iface, strength, rssi, upload, download, vpn, zone_name)
    output_json(icon, tooltip, bool(vpn))


if __name__ == "__main__":
    main()
