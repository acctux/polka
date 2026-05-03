#!/usr/bin/env python3
import json
import subprocess
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
    return (
        zone_output.splitlines()[0].split(None, 1)[0] if zone_output else "Firewall Off"
    )


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
    for line in info:
        line = line.lstrip()
        if line.startswith("rx bitrate:"):
            rx_bitrate = float(line.split()[2])
        elif line.startswith("tx bitrate:"):
            tx_bitrate = float(line.split()[2])
        elif line.startswith("SSID:"):
            network = line.split()[1]
        elif line.startswith("signal:"):
            rssi = line.split()[1]
            iwd_strength = max(0, min(100, 100 - ((int(rssi) + 100) // 2)))
    rx_bitrate_mb = rx_bitrate / 8
    tx_bitrate_mb = tx_bitrate / 8
    return network, rx_bitrate_mb, tx_bitrate_mb, iwd_strength


def main(service="None"):
    iface = find_interface()
    vpn = run(["wg", "show", "interfaces"])
    zone_name = get_firewalld_zone()
    net_name, tx, rx, strength = parse_info_joint(iface)
    if is_running("NetworkManager"):
        service = "NetworkManager"
        strength = parse_info_nm()
    elif is_running("iwd"):
        service = "IWD"
    icon = ICONS[min(strength // 20, 4)]
    tooltip = [
        f"󱨑 : {zone_name}",
        f"󰣖 : {service}\t\n",
        f"󰀂 : {net_name}\t",
        f"{icon} : {strength}%\t",
        f"↑ : {int(rx)}M\t",
        f"↓ : {int(tx)}M\t",
    ]
    if vpn:
        tooltip.insert(0, f"󰖂 : {vpn}")
    print(
        json.dumps(
            {
                "text": icon,
                "tooltip": "\n".join(tooltip),
                "class": "vpn" if vpn else "",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
