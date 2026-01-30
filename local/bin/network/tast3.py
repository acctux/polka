import dbus
import subprocess
import time
from pathlib import Path


class NetworkManager:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.manager = dbus.Interface(
            self.bus.get_object("net.connman.iwd", "/"),
            "org.freedesktop.DBus.ObjectManager",
        )
        self.iwctl_cmd = ["iwctl"]
        self.device_name = "wlan0"
        self.network_paths = []

    def _run_command(self, command):
        result = subprocess.run(
            self.iwctl_cmd + command, capture_output=True, text=True
        )
        if result.returncode != 0:
            raise Exception(f"Error executing command: {result.stderr}")
        return result.stdout

    def find_device(self):
        self.device_path = next(
            (
                path
                for path, interfaces in self.manager.GetManagedObjects().items()
                if "net.connman.iwd.Station" in interfaces
            ),
            None,
        )
        if not self.device_path:
            raise Exception("No devices found")

    def scan_networks(self):
        device = dbus.Interface(
            self.bus.get_object("net.connman.iwd", self.device_path),
            "net.connman.iwd.Station",
        )
        device.Scan()
        print("Scanning for networks...")
        time.sleep(5)  # Allow time for scanning

    def get_networks(self):
        return self._run_command(["station", self.device_name, "get-networks"])

    def assign_icons(self, network_type):
        icon_map = {
            "*\x1b[1;90m***\x1b[0m": "󰤯",
            "**\x1b[1;90m**\x1b[0m": "󰤟",
            "***\x1b[1;90m*\x1b[0m": "󰤢",
            "****": "󰤥",
        }
        return icon_map.get(network_type, "")  # Default icon if not found

    def filter_valid_networks(self, networks_raw: str) -> list[tuple[str, str]]:
        networks = []
        raw_lines = networks_raw.splitlines()
        for line in raw_lines:
            line = line.strip()
            if (
                "Network name" in line and "Security" in line and "Signal" in line
            ) or "------------------------------" in line:
                continue
            if "psk" in line or "WEP" in line:  # Only include secure networks
                parts = line.split()
                if parts:
                    if parts[0] == "\x1b[0m":
                        if parts[1] == "\x1b[1;90m>":
                            networks.append((parts[3], parts[5]))
                        else:
                            networks.append((parts[1], parts[3]))
                    else:
                        networks.append((parts[0], parts[2]))
        networks.append(("Rescan", ""))  # Add "Rescan" option at the end
        return networks

    def connect_to_selected_network(self, selected_network_name):
        selected_network_path = next(
            (
                path
                for path in self.network_paths
                if self.manager.GetManagedObjects()[path]["net.connman.iwd.Network"][
                    "Name"
                ]
                == selected_network_name
            ),
            None,
        )
        if not selected_network_path:
            raise Exception(f"Network {selected_network_name} not found")
        network = dbus.Interface(
            self.bus.get_object("net.connman.iwd", selected_network_path),
            "net.connman.iwd.Network",
        )
        try:
            print(f"Connecting to {selected_network_name}...")
            network.Connect()
            print("Connection successful!")
        except dbus.exceptions.DBusException as e:
            print(f"Connection failed: {e}")


def run_fuzzel(options_str, width: int | None = None, num_lines: int | None = None):
    HOME = Path.home()
    args = [
        "fuzzel",
        f"--width={width}",
        "--dmenu",
        f"--config={HOME}/.config/fuzzel/vpnmenu.ini",
    ]
    if num_lines:
        args.insert(2, f"--lines={num_lines}")
    try:
        return subprocess.run(
            args, input=options_str, text=True, capture_output=True
        ).stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running fuzzel: {e}")
        return ""


def run_once(nm: NetworkManager):
    nm.find_device()
    nm.scan_networks()
    networks_raw = nm.get_networks()
    networks = nm.filter_valid_networks(networks_raw)
    network_with_icons = [
        f"{network[0]} {nm.assign_icons(network[1])}" for network in networks
    ]
    options_str = "\n".join(network_with_icons)
    options_str = options_str.strip() + "\nRescan"
    selected_network = run_fuzzel(
        options_str,
        max((len(network[0]) for network in networks), default=0) + 4,
        len(networks),
    )
    return selected_network


if __name__ == "__main__":
    nm = NetworkManager()
    while True:
        selected_network = run_once(nm)
        if selected_network == "Rescan":
            print("Rescanning networks...")
            continue
        if selected_network:
            nm.connect_to_selected_network(selected_network)
            break
        else:
            print("No network selected.")
            break
