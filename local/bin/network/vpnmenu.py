#!/usr/bin/env python3
import subprocess
from pathlib import Path


def vpn_menu(
    path=Path("/var/cache/mysysinfo/vpn.list"),
    fuzzel_config=Path.home() / ".config/fuzzel/fav-menu.ini",
):
    def run(cmd: list, sudo=False):
        if sudo:
            cmd = ["sudo", "-A"] + cmd
        return subprocess.run(cmd, text=True, capture_output=True)

    def set_network_and_named(
        ipv4: bool, script_dir: Path = Path(__file__).resolve().parent
    ):
        val = "1" if ipv4 else "0"
        run(["sysctl", "-w", f"net.ipv6.conf.all.disable_ipv6={val}"], sudo=True)
        run(["sysctl", "-w", f"net.ipv6.conf.default.disable_ipv6={val}"], sudo=True)
        named_conf = Path("/etc/named.conf")
        target = script_dir / f"namedipv{4 if ipv4 else 6}.conf"
        if named_conf.read_text() != target.read_text():
            if run(["cp", str(target), str(named_conf)], sudo=True).returncode == 0:
                run(["systemctl", "restart", "named"], sudo=True)

    options = path.read_text().splitlines() + ["─────", "Disconnect", "Cancel"]
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
    for line in run(["wg", "show"], sudo=True).stdout.splitlines():
        if line.startswith("interface:"):
            run(["wg-quick", "down", line.split(":", 1)[1].strip()], sudo=True)
    set_network_and_named(ipv4=False)
    if choice == "Disconnect":
        return
    success = run(["wg-quick", "up", choice], sudo=True).returncode == 0
    set_network_and_named(ipv4=success)


if __name__ == "__main__":
    vpn_menu()
