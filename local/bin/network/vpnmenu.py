#!/usr/bin/env python3
import subprocess
from pathlib import Path
import sys


def vpn_menu(
    path=Path("/var/cache/mysysinfo/vpn.list"),
    fuzzel_config=Path.home() / ".config/fuzzel/fav-menu.ini",
    cli_choice: str | None = None,
):
    def run(cmd: list, sudo=False):
        if sudo:
            cmd = ["sudo", "-A"] + cmd
        print(f"Running {cmd}")
        return subprocess.run(cmd, text=True, capture_output=True)

    def set_network_and_named(ipv4: bool):
        named_conf = Path("/etc/named.conf")
        namedconf_dir: Path = Path(__file__).resolve().parent / "namedconf"
        target = namedconf_dir / f"namedipv{4 if ipv4 else 6}.conf"

        current = subprocess.run(
            ["sudo", "cat", str(named_conf)],
            text=True,
            capture_output=True,
        ).stdout

        if current != target.read_text():
            if run(["cp", str(target), str(named_conf)], sudo=True).returncode == 0:
                run(["systemctl", "restart", "named"], sudo=True)

    options = path.read_text().splitlines() + ["─────", "Disconnect", "Cancel"]

    # -----------------------------
    # CLI MODE (no fuzzel needed)
    # -----------------------------
    if cli_choice is not None:
        choice = cli_choice
    else:
        choice = subprocess.run(
            [
                "fuzzel",
                "--dmenu",
                f"--width={max(map(len, options)) + 1}",
                "--lines",
                str(len(options)),
                "--config",
                str(fuzzel_config),
                "--x-margin=80",
            ],
            input="\n".join(options),
            text=True,
            capture_output=True,
        ).stdout.strip()

    if choice in ("", "Cancel"):
        return

    # disconnect existing VPN
    for line in run(["wg", "show"], sudo=True).stdout.splitlines():
        if line.startswith("interface:"):
            run(["wg-quick", "down", line.split(":", 1)[1].strip()], sudo=True)

    set_network_and_named(ipv4=False)

    if choice == "Disconnect":
        return

    success = run(["wg-quick", "up", choice], sudo=True).returncode == 0
    set_network_and_named(ipv4=success)


if __name__ == "__main__":
    cli_choice = sys.argv[1] if len(sys.argv) > 1 else None
    vpn_menu(cli_choice=cli_choice)
