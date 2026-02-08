#!/usr/bin/env python3
import sys
import subprocess


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


def disconnect_current_interface() -> None:
    current = [name for name in get_active_interfaces()]
    if current:
        for iface in current:
            run_cmd(["wg-quick", "down", iface])
            print(f"\nDisconnected successfully from {iface}")
    else:
        print("No active interfaces found to disconnect.")


def main() -> None:
    if len(sys.argv) != 2:
        disconnect_current_interface()
        return
    disconnect_current_interface()
    config = sys.argv[1]
    result = run_cmd(["wg-quick", "up", config])
    if result.returncode != 0:
        sys.exit(1)
    print(f"\nConnected to {config}")


if __name__ == "__main__":
    main()

