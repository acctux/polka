#!/usr/bin/env python3
import time
import subprocess
import sys
import dbus
from pathlib import Path

HOME = Path.home()
FUZZEL_CONFIG = HOME / ".config/fuzzel/netmenu.ini"
SLEEP_TIME = 2
MAIN_CHOICES = ["WiFi", "VPN", "Cancel"]


class NetworkManager:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.manager = dbus.Interface(
            self.bus.get_object("net.connman.iwd", "/"),
            "org.freedesktop.DBus.ObjectManager",
        )
        self.device_name = "wlan0"

    def _run_command(self, command: list[str]) -> str:
        result = subprocess.run(["iwctl"] + command, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Error executing command: {result.stderr}")
        return result.stdout

    def find_device(self):
        device_path = next(
            (
                path
                for path, interfaces in self.manager.GetManagedObjects().items()
                if "net.connman.iwd.Station" in interfaces
            ),
            None,
        )
        if not device_path:
            raise Exception("No devices found")
        self.device_path = device_path

    def scan_networks(self, sleep_time: int):
        device = dbus.Interface(
            self.bus.get_object("net.connman.iwd", self.device_path),
            "net.connman.iwd.Station",
        )
        device.Scan()
        time.sleep(sleep_time)

    def get_networks(self) -> str:
        return self._run_command(["station", self.device_name, "get-networks"])

    def filter_valid_networks(self, networks_raw: str) -> list[tuple[str, str]]:
        networks = []
        for line in networks_raw.splitlines():
            line = line.strip()
            if "psk" in line or "WEP" in line:
                parts = line.split()
                if parts:
                    if parts[0] == "\x1b[0m":
                        if parts[1] == "\x1b[1;90m>":
                            print("current")
                            networks.append((parts[3], parts[5]))
                        else:
                            networks.append((parts[1], parts[3]))
                    else:
                        networks.append((parts[0], parts[2]))
        return networks

    def connect_to_network(self, ssid: str, password: str):
        command = ["station", self.device_name, "connect", ssid]
        if password:
            command.extend(["--passphrase", password])
        self._run_command(command)


def run_fuzzel(options: list[str], config: Path) -> str:
    lines = len(options)
    max_chars = len(max(options, key=len))
    result = subprocess.run(
        [
            "fuzzel",
            "--dmenu",
            "--hide-prompt",
            f"--width={max_chars + 1}",
            "--lines",
            str(lines),
            "--config",
            str(config),
        ],
        input="\n".join(options),
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def get_wifi_password_via_zenity(ssid: str) -> str:
    result = subprocess.run(
        ["zenity", f"--title=Enter password for {ssid}"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def handle_strength(strength_str: str):
    if strength_str == "****":
        return "󰤨"
    elif strength_str == "***\x1b[1;90m*\x1b[0m":
        return "󰤥"
    elif strength_str == "**\x1b[1;90m**\x1b[0m":
        return "󰤟"
    elif strength_str == "*\x1b[1;90m***\x1b[0m":
        return "󰤯"
    return strength_str


def handle_wifi(nm: NetworkManager, sleep_time: int, config):
    while True:
        nm.find_device()
        networks_raw = nm.get_networks()
        networks = nm.filter_valid_networks(networks_raw)
        options = []
        for network in networks:
            sig_strength = handle_strength(network[1])
            options.append(f"{network[0]} {sig_strength}")
        max_length = max(len(option) for option in options)
        separator = "_" * (max_length + 3)
        lines = options + [separator, "Scan", "Back"]
        selected_network = run_fuzzel(lines, config)
        if selected_network in ("Back", ""):
            break
        if selected_network == "Scan":
            print("Rescanning networks...")
            nm.scan_networks(sleep_time)
            continue
        password = get_wifi_password_via_zenity(selected_network)
        if password:
            nm.connect_to_network(selected_network, password)
            print(f"Connected to {selected_network}")
        else:
            print("Failed to get password or canceled.")


def run_cmd(cmd: list[str], use_sudo: bool = False) -> subprocess.CompletedProcess:
    if use_sudo:
        cmd = ["sudo", "-A"] + cmd
    return subprocess.run(cmd, capture_output=True, text=True)


def get_active_interfaces() -> list[str]:
    result = run_cmd(["wg", "show"], use_sudo=True)
    if result.returncode != 0:
        return []
    interfaces = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("interface:"):
            iface = line.split(":", 1)[1].strip()
            interfaces.append(iface)
    return interfaces


def disconnect_current_interface() -> None:
    current = [name for name in get_active_interfaces()]
    if current:
        for iface in current:
            run_cmd(["wg-quick", "down", iface], use_sudo=True)
            print(f"\nDisconnected successfully from {iface}")
    else:
        print("No active interfaces found to disconnect.")


def handle_vpn(config):
    list_path = Path("/run/wireguard/connections.list")
    if list_path.exists():
        with open(list_path, "r") as f:
            vpns = f.read().strip().splitlines()
        vpns = vpns + ["──────", "Disconnect"]
        choice = run_fuzzel(vpns, config)
        if not choice:
            sys.exit(1)
        if choice == "Back":
            return
        elif choice == "Disconnect":
            disconnect_current_interface()
            sys.exit(0)
        else:
            disconnect_current_interface()
            result = run_cmd(["wg-quick", "up", choice], use_sudo=True)
            if result.returncode != 0:
                sys.exit(1)
            print(f"\nConnected to {choice}")
            sys.exit(0)


def main():
    while True:
        choice = run_fuzzel(MAIN_CHOICES, config=FUZZEL_CONFIG)
        if choice == "WiFi":
            handle_wifi(NetworkManager(), sleep_time=SLEEP_TIME, config=FUZZEL_CONFIG)
        elif choice == "VPN":
            handle_vpn(config=FUZZEL_CONFIG)
        elif choice in ("Cancel", ""):
            sys.exit(0)


if __name__ == "__main__":
    main()
