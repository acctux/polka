import dbus
import sys
import time
import subprocess
from pathlib import Path


class NetworkManager:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.manager = dbus.Interface(
            self.bus.get_object("net.connman.iwd", "/"),
            "org.freedesktop.DBus.ObjectManager",
        )
        self.device_path = None
        self.network_paths = []

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
            print("No devices found.")
            sys.exit(1)

    def scan_networks(self):
        device = dbus.Interface(
            self.bus.get_object("net.connman.iwd", self.device_path),
            "net.connman.iwd.Station",
        )
        device.Scan()
        print("Scanning for networks...")
        time.sleep(5)

    def list_networks(self) -> tuple[list[str], int]:
        self.network_paths = [
            path
            for path, interfaces in self.manager.GetManagedObjects().items()
            if "net.connman.iwd.Network" in interfaces
        ]
        if not self.network_paths:
            print("No networks found.")
            sys.exit(1)
        print("\nAvailable networks:")
        networks = []
        max_network_name_len = 0  # Initialize the variable to store max length
        for path in self.network_paths:
            network = self.manager.GetManagedObjects()[path]["net.connman.iwd.Network"]
            network_name = network["Name"]
            network_type = network["Type"]
            max_network_name_len = max(max_network_name_len, len(network_name))
            print(f"Network path: {path}, Name: {network_name}, Type: {network_type}")
            networks.append(network_name)
        print(f"\nMax length of network names: {max_network_name_len}")
        return networks, max_network_name_len

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
            print(f"Network {selected_network_name} not found.")
            sys.exit(1)
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


def run_fuzzel(options_str: str, width: int, num_lines: int | None = None) -> str:
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
        result = subprocess.run(
            args, input=options_str, text=True, capture_output=True
        ).stdout.strip()
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running fuzzel: {e}")
        return ""


if __name__ == "__main__":
    nm = NetworkManager()
    nm.find_device()
    nm.scan_networks()
    networks, max_chars = nm.list_networks()
    selected_network = run_fuzzel("\n".join(networks), max_chars + 2, len(networks))
    if selected_network:
        nm.connect_to_selected_network(selected_network)
    else:
        print("No network selected.")

