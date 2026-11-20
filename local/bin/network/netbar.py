#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path

ICONS = ["󰤯", "󰤟", "󰤢", "󰤥", "󰤨"]


def run(cmd: list) -> str:
    try:
        return subprocess.check_output(
            cmd, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return ""


def is_running(service_name: str) -> bool:
    try:
        code = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            check=False,
        ).returncode
        return code == 0
    except subprocess.CalledProcessError:
        return False


def get_ufw_status() -> str:
    ufw_status = "UFW Missing"
    if is_running("ufw"):
        for line in Path("/etc/ufw/ufw.conf").read_text().splitlines():
            line = line.strip()
            if line.startswith("ENABLED="):
                enabled = line.split("=", 1)[1].lower()
                if enabled == "yes":
                    ufw_status = "UFW Enabled"
                elif enabled == "no":
                    ufw_status = "UFW Disabled"
    else:
        ufw_status = "UFW Not Running"
    return ufw_status


def find_interface() -> str:
    for dev in Path("/sys/class/net").iterdir():
        if (dev / "wireless").exists():
            return dev.name
    return ""


def parse_info_nm() -> int:
    wifi_list = run(["nmcli", "-f", "SIGNAL,CHAN,ACTIVE", "device", "wifi", "list"])
    for line in wifi_list.splitlines():
        if "yes" in line:
            strength = int(line.split()[0])
            return strength
    return 0


def parse_info_joint(iface: str) -> tuple[str, float, float, int]:
    info = run(["iw", "dev", iface, "link"]).splitlines()
    rx_bitrate = tx_bitrate = iwd_strength = 0
    network = "Disconnected"
    for line in info:
        line = line.lstrip()
        if line.startswith("rx bitrate:"):
            rx_bitrate = float(line.split()[2])
        elif line.startswith("tx bitrate:"):
            tx_bitrate = float(line.split()[2])
        elif line.startswith("SSID:"):
            network = line.split("SSID:", 1)[1].strip()
        elif line.startswith("signal:"):
            rssi = int(line.split()[1])
            iwd_strength = max(0, min(100, 100 - ((rssi + 100) // 2)))
    rx_bitrate_mb = rx_bitrate / 8
    tx_bitrate_mb = tx_bitrate / 8
    return network, rx_bitrate_mb, tx_bitrate_mb, iwd_strength


def main():
    iface = find_interface()
    vpn = run(["wg", "show", "interfaces"])
    firewall_status = get_ufw_status()
    net_name, tx, rx, strength = parse_info_joint(iface)
    if is_running("NetworkManager"):
        service = "NetworkManager"
        strength = parse_info_nm()
    elif is_running("iwd"):
        service = "IWD"
    else:
        service = "No WiFi Service Running"
    icon = ICONS[min(strength // 20, 4)]
    tooltip = [
        f"󰖂 : {vpn if vpn else 'No VPN'}",
        f"󱨑 : {firewall_status}",
        f"󰣖 : {service}\t\n",
        f"󰀂 : {net_name}\t",
        f"{icon} : {strength}%\t",
        f"↑ : {int(rx)}M\t",
        f"↓ : {int(tx)}M\t",
    ]
    waybar_info = {
        "text": icon,
        "tooltip": "\n".join(tooltip),
        "class": "vpn" if vpn else "",
    }
    print(json.dumps(waybar_info, ensure_ascii=False))


if __name__ == "__main__":
    main()
