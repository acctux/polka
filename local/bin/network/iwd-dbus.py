import subprocess
import time
from pathlib import Path


def run_fuzzel(
    options_str: str,
    width: int,
    num_lines: int | None = None,
) -> str:
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


def select_network(options: list[tuple[str, str]]):
    print("Available Networks:")
    icons = ["󰤯", "󰤟", "󰤢", "󰤥", "󰤨"]
    icon_map = {
        "*\x1b[1;90m***\x1b[0m": icons[1],
        "**\x1b[1;90m**\x1b[0m": icons[2],
        "***\x1b[1;90m*\x1b[0m": icons[3],
        "****": icons[4],
    }
    network_strings: list[str] = []
    for option in options:
        network_string = f"{option[0]} {icon_map.get(option[1], '')}"
        network_strings.append(network_string)
    max_chars = max(len(network_string) for network_string in network_strings) + 1
    network_list_display = "\n".join(network_strings)
    choice = run_fuzzel(network_list_display, max_chars, len(options))
    if choice:
        for option in options:
            if f"{option[0]} {icon_map.get(option[1], '')}" == choice:
                return option
    print("Invalid selection.")
    return None


class IwctlWrap:
    def __init__(self, device_name="wlan0"):
        self.iwctl_cmd = ["iwctl"]
        self.device_name = device_name

    def _run_command(self, command):
        full_command = self.iwctl_cmd + command
        result = subprocess.run(full_command, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(
                f"Error executing command: {' '.join(full_command)}\n{result.stderr}"
            )
        return result.stdout

    def list_devices(self):
        return self._run_command(["device", "list"])

    def scan_networks(self):
        return self._run_command(["station", self.device_name, "scan"])

    def get_networks(self):
        return self._run_command(["station", self.device_name, "get-networks"])

    def connect_to_network(self, ssid, passphrase=None):
        command = ["station", self.device_name, "connect", ssid]
        if passphrase:
            command += ["--passphrase", passphrase]
        return self._run_command(command)

    def toggle_device_power(self, power_on=True):
        status = "on" if power_on else "off"
        return self._run_command(
            ["device", self.device_name, "set-property", "Powered", status]
        )

    def filter_valid_networks(self, networks_raw: str) -> list[tuple[str, str]]:
        networks = []
        raw_lines = networks_raw.splitlines()
        for line in raw_lines:
            line = line.strip()
            if (
                "Network name" in line and "Security" in line and "Signal" in line
            ) or "------------------------------" in line:
                continue
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
        return networks


def main():
    iwctl_wrap = IwctlWrap()

    try:
        iwctl_wrap.list_devices()
        iwctl_wrap.toggle_device_power(True)
        iwctl_wrap.scan_networks()
        time.sleep(5)
        networks_raw = iwctl_wrap.get_networks()
        networks = iwctl_wrap.filter_valid_networks(networks_raw)
        if not networks:
            print("No valid networks found.")
            return
        selected_network = select_network(networks)
        if selected_network:
            passphrase = input(f"Enter passphrase for {selected_network[0]} (if any): ")
            iwctl_wrap.connect_to_network(selected_network[0], passphrase)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
