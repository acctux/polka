#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
from network import NetworkManager

HOME = Path.home()
FUZZEL_CONFIG = HOME / ".config/fuzzel/vpnmenu.ini"
SLEEP_TIME = 3
MAIN_CHOICES = ["WiFi", "VPN", "Cancel"]


def run_fuzzel_menu(options: list[str], lines: int) -> str:
    result = subprocess.run(
        [
            "fuzzel",
            "--dmenu",
            "--hide-prompt",
            "--lines",
            str(lines),
            "--config",
            str(FUZZEL_CONFIG),
        ],
        input="\n".join(options),
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def handle_wifi():
    nm = NetworkManager(SLEEP_TIME)
    while True:
        selected_network = nm.run_once()
        if selected_network in ("Back", ""):
            break
        if selected_network == "Scan":
            print("Rescanning networks...")
            nm.notify_send(f"Scanning {SLEEP_TIME} seconds.")
            nm.scan_networks(SLEEP_TIME)
            continue
        nm.connect_to_selected_network(selected_network)
        break


def handle_vpn():
    connections_file = Path("/run/wireguard/connections.list")
    if not connections_file.exists():
        print(f"{connections_file} does not exist.")
        sys.exit(1)
    with connections_file.open() as f:
        vpns = [line.strip() for line in f if line.strip()]
    vpns.append("Back")
    vpn_choice = run_fuzzel_menu(vpns, len(vpns))
    if vpn_choice and vpn_choice != "Back":
        subprocess.run(
            [
                "kitty",
                "sudo",
                "python3",
                str(HOME / ".local/bin/protonvpn/protonconnect.py"),
                vpn_choice,
            ]
        )


def main():
    while True:
        choice = run_fuzzel_menu(MAIN_CHOICES, len(MAIN_CHOICES))
        if choice == "WiFi":
            handle_wifi()
        elif choice == "VPN":
            handle_vpn()
        elif choice in ("Cancel", ""):
            sys.exit(0)


if __name__ == "__main__":
    main()
