#!/usr/bin/env python3
import time
import subprocess
import sys
import dbus
from pathlib import Path

HOME = Path.home()
FUZZEL_CONFIG = HOME / ".config/fuzzel/vpnmenu.ini"
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
                            networks.append((parts[3], parts[5]))
                        else:
                            networks.append((parts[1], parts[3]))
                    else:
                        networks.append((parts[0], parts[2]))
        networks.insert(0, ("Scan", ""))
        networks.append(("Back", ""))
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
            f"--width={max_chars + 2}",
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
    try:
        result = subprocess.run(
            ["zenity", f"--title=Enter password for {ssid}"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except FileNotFoundError:
        print("Zenity is not installed.")
        return ""


def handle_wifi(nm: NetworkManager, sleep_time: int, config):
    while True:
        nm.find_device()
        networks_raw = nm.get_networks()
        networks = nm.filter_valid_networks(networks_raw)
        options = [network[0] for network in networks]
        selected_network = run_fuzzel(options, config)
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


def run_cmd(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def get_active_interfaces() -> list[str]:
    result = run_cmd(["wg", "show"])
    if result.returncode != 0:
        return []
    interfaces = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("interface:"):
            iface = line.split(":", 1)[1].strip()
            interfaces.append(iface)
    return interfaces


def handle_vpn(config):
    connections_file = Path("/run/wireguard/connections.list")
    if not connections_file.exists():
        print(f"{connections_file} does not exist.")
        sys.exit(1)
    with connections_file.open() as f:
        vpns = [line.strip() for line in f if line.strip()]
    vpns.append("Back")
    vpn_choice = run_fuzzel(vpns, config)
    if vpn_choice and vpn_choice != "Back":
        current = [name for name in get_active_interfaces()]
        if current:
            for iface in current:
                run_cmd(["wg-quick", "down", iface], check=True)
                print(f"\nDisconnected successfully from {iface}")
        if len(sys.argv) != 2:
            return
        config = sys.argv[1]
        result = run_cmd(["wg-quick", "up", config])
        if result.returncode != 0:
            sys.exit(1)
        print(f"\nConnected to {config}")


def main():
    while True:
        choice = run_fuzzel(MAIN_CHOICES, config=FUZZEL_CONFIG)
        if choice == "WiFi":
            nm = NetworkManager()
            handle_wifi(nm, sleep_time=SLEEP_TIME, config=FUZZEL_CONFIG)
        elif choice == "VPN":
            handle_vpn(config=FUZZEL_CONFIG)
        elif choice in ("Cancel", ""):
            sys.exit(0)


if __name__ == "__main__":
    main()
