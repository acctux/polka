#!/usr/bin/env python3
import json
import subprocess
import time
from pathlib import Path

CACHE = Path("/tmp/waybar-wifi.json")
ICONS = ["󰤯", "󰤟", "󰤢", "󰤥", "󰤨"]


def run(cmd: list) -> str:
    try:
        return subprocess.check_output(
            cmd, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return ""


def get_firewalld_zone() -> str:
    zone_output = run(["firewall-cmd", "--get-active-zones"])
    return zone_output.splitlines()[0].split(None, 1)[0] if zone_output else "off"


def is_running(service_name: str) -> bool:
    try:
        return (
            subprocess.run(
                ["systemctl", "is-active", service_name], capture_output=True, text=True
            ).returncode
            == 0
        )
    except subprocess.CalledProcessError:
        return False


def load_previous_stats() -> dict:
    try:
        return json.loads(CACHE.read_text()) if CACHE.exists() else {}
    except json.JSONDecodeError:
        return {}


def parse_info_nm() -> dict:
    wifi_list = run(
        ["nmcli", "-f", "SSID,SIGNAL,CHAN,ACTIVE", "device", "wifi", "list"]
    )
    tx = run(["cat", "/sys/class/net/wlan0/statistics/tx_bytes"]) or "0"
    rx = run(["cat", "/sys/class/net/wlan0/statistics/rx_bytes"]) or "0"
    for line in wifi_list.splitlines()[1:]:
        if "yes" in line:
            ssid, strength = line.split()[0], int(line.split()[1])
            return {
                "net_name": ssid,
                "strength": strength,
                "tx": int(tx),
                "rx": int(rx),
            }
    return {"net_name": "No Network", "strength": 0, "tx": int(tx), "rx": int(rx)}


def parse_info_iwd() -> dict:
    def find_wifi_interface_iwd() -> str:
        for dev in Path("/sys/class/net").iterdir():
            if (dev / "wireless").exists():
                return dev.name
        return ""

    iface = find_wifi_interface_iwd()
    ssid_info = run(["iwctl", "station", iface, "show"]).splitlines()
    network = next(
        (line.split()[2] for line in ssid_info if "Connected network" in line),
        "Unknown Network",
    )
    station_info = run(["iw", "dev", iface, "station", "dump"]).splitlines()
    iwd_strength = rx = tx = 0
    for line in station_info:
        if "signal avg:" in line:
            rssi = int(line.split(":")[1].strip().split()[0])
            iwd_strength = max(0, min(100, 100 - ((-rssi + 100) // 2)))
        if "rx bytes:" in line:
            rx = int(line.split(":")[1].strip())
        if "tx bytes:" in line:
            tx = int(line.split(":")[1].strip())
    return {"net_name": network, "strength": iwd_strength, "tx": tx, "rx": rx}


def save_stats(rx: float, tx: float) -> None:
    try:
        CACHE.write_text(json.dumps({"rx": rx, "tx": tx, "t": time.time()}))
    except Exception as e:
        print(f"Error saving stats: {e}")


def compute_speeds(prev, rx, tx) -> tuple[float, float]:
    if prev and "t" in prev and "tx" in prev and "rx" in prev:
        dt = time.time() - prev.get("t", 0)
        if dt > 0.5:
            rx_speed = (rx - prev.get("rx", 0)) / dt
            tx_speed = (tx - prev.get("tx", 0)) / dt
            return rx_speed, tx_speed
    return 0.0, 0.0


def build_tooltip(service: str, wifi_dict: dict, vpn: str, zone_name: str) -> str:
    tooltip = [
        f"{service}\t",
        f"{wifi_dict['net_name']}\t",
        f"{wifi_dict['strength']}%\t",
        f"↑{wifi_dict['tx'] / 1_048_576:.1f}M\t",
        f"↓{wifi_dict['rx'] / 1_048_576:.1f}M\t",
        f"{zone_name} 󱨑",
    ]
    if vpn:
        tooltip.insert(0, vpn)
    return "\n".join(tooltip)


def output_json(icon, tooltip, vpn_active) -> None:
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


def main(wifi_dict={}, service="None"):
    vpn = run(["wg", "show", "interfaces"])
    zone_name = get_firewalld_zone()
    prev = load_previous_stats()
    if is_running("NetworkManager"):
        service = "NetworkManager"
        wifi_dict = parse_info_nm()
    elif is_running("iwd"):
        service = "IWD"
        wifi_dict = parse_info_iwd()
    wifi_dict["tx"], wifi_dict["rx"] = compute_speeds(
        prev, wifi_dict["rx"], wifi_dict["tx"]
    )
    tooltip = build_tooltip(service, wifi_dict, vpn, zone_name)
    save_stats(wifi_dict["rx"], wifi_dict["tx"])
    output_json(ICONS[min(wifi_dict["strength"] // 20, 4)], tooltip, vpn)


if __name__ == "__main__":
    main()
