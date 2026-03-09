#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

TLP_CONF = Path("/etc/tlp.d/99-mydefaults.conf")
MYDEFAULTS_CONF = Path("/etc/tlp.d/mydefaults.conf")
TLP_CONTENT = """\
TLP_DEFAULT_MODE=BAT
TLP_PERSISTENT_DEFAULT=1
"""

MYDEFAULTS_CONTENT = """\
CPU_ENERGY_PERF_POLICY_ON_BAT=power
CPU_ENERGY_PERF_POLICY_ON_AC=balance_power
PCIE_ASPM_ON_BAT=powersave
DISK_DEVICES="nvme0n1 nvme1n1"
PCIE_ASPM_ON_AC=powersave
AHCI_RUNTIME_PM_ON_AC=auto
RUNTIME_PM_ON_AC=auto
RUNTIME_PM_ENABLE="01:00.0"
DEVICES_TO_ENABLE_ON_STARTUP="wifi"
"""


def write_file(path: Path, content: str):
    try:
        with open(path, "w") as f:
            f.write(content)
        print(f"Wrote {path}")
    except PermissionError:
        print(f"Permission denied: cannot write {path}")
        sys.exit(1)


def delete_file(path: Path):
    if path.exists():
        path.unlink()
        print(f"Deleted {path}")
    else:
        print(f"{path} does not exist, skipping")


def reload_tlp():
    try:
        subprocess.run(["systemctl", "restart", "tlp.service"], check=True)
        print("TLP reloaded successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to reload TLP: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} {{batmode|default|none}}")
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "batmode":
        write_file(TLP_CONF, TLP_CONTENT)
    elif mode == "default":
        write_file(MYDEFAULTS_CONF, MYDEFAULTS_CONTENT)
    elif mode == "none":
        delete_file(TLP_CONF)
        delete_file(MYDEFAULTS_CONF)
    else:
        print(f"Usage: {sys.argv[0]} {{batmode|default|none}}")
        sys.exit(1)
    reload_tlp()


if __name__ == "__main__":
    main()
