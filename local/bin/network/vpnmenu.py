#!/usr/bin/env python3
import logging
import subprocess
import sys
import time
from pathlib import Path
import psutil

FUZZEL_CONFIG = Path.home() / ".config/fuzzel/waybar.ini"
NAMEDCONF_DIR = Path(__file__).resolve().parent / "namedconf"
WIFI_SERVICES = {
    "iwd.service": "NetworkManager.service",
    "NetworkManager.service": "iwd.service",
}


#########################
# LOGGING
#########################
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.INFO: "\033[36m",
        logging.WARNING: "\033[93m",
        logging.ERROR: "\033[31m",
    }
    RESET = "\033[0m"
    NAME_COLOR = "\033[93m"

    def format(self, record: logging.LogRecord) -> str:
        name = f"{self.NAME_COLOR}{record.name}{self.RESET}"
        msg = f"{self.COLORS.get(record.levelno, '')}{record.getMessage()}{self.RESET}"
        return f"{name}: {msg}"


def get_logger(name: str = "NetworkManager") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stderr)
        h.setFormatter(ColorFormatter())
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


log = get_logger()


#########################
# ALL-IN-ONE MANAGER
#########################
class NetworkManager:
    def __init__(
        self,
        fuzzel_config: Path = FUZZEL_CONFIG,
        namedconf_dir: Path = NAMEDCONF_DIR,
        wifi_services: dict[str, str] = WIFI_SERVICES,
    ):
        self.vpn_list = Path("/var/cache/mysysinfo/vpn.list")
        self.fuzzel_config = fuzzel_config
        self.namedconf_dir = namedconf_dir
        self.wifi_services = wifi_services

    def _run(
        self,
        cmd: list[str],
        input: str | None = None,
    ) -> subprocess.CompletedProcess:
        log.info(f"run: {' '.join(cmd)}")
        return subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            input=input,
        )

    def _sudo(
        self,
        cmd: list[str],
    ) -> subprocess.CompletedProcess:
        full = ["sudo", "-A"] + cmd
        log.info(f"sudo: {' '.join(full)}")
        return subprocess.run(
            full,
            text=True,
            capture_output=True,
        )

    def _ui(
        self,
        cmd: list[str],
    ) -> int:
        log.info(f"ui: {' '.join(cmd)}")
        return subprocess.run(cmd).returncode

    def fuzzel_menu(
        self,
        options: list[str],
    ) -> str:
        menu_text = "\n".join(options)
        width = max(map(len, options))
        lines = str(len(options))
        cmd = [
            "fuzzel",
            "--dmenu",
            f"--width={width}",
            "--x-margin=60",
            "--lines",
            lines,
            "--config",
            str(self.fuzzel_config),
        ]
        return self._run(cmd, input=menu_text).stdout.strip()

    def reset_wifi(self) -> None:
        for current, target in self.wifi_services.items():
            cmd = ["systemctl", "is-active", current]
            if self._run(cmd).stdout.strip() != "active":
                continue
            cmd = [
                "zenity",
                "--question",
                "--text",
                f"{current} running. Switch to {target}?",
            ]
            if self._ui(cmd) != 0:
                log.info("Wi-Fi reset aborted by user.")
                return
            log.info(f"Switching from {current} to {target}...")
            result = self._sudo(["systemctl", "stop", current])
            if result != 0:
                return
            self._sudo(["modprobe", "-r", "rtw89_8852be"])
            time.sleep(1)
            self._sudo(["modprobe", "rtw89_8852be"])
            time.sleep(10)
            self._sudo(["systemctl", "start", target])
            log.info(f"Switched from {current} to {target} successfully.")
            return
        log.info("Neither iwd nor NetworkManager is active. No changes made.")

    # --- VPN ---
    def _set_network(self, ipv4: bool) -> subprocess.CompletedProcess | None:
        val = "1" if ipv4 else "0"
        for iface in ["all", "default", "lo"]:
            result = self._sudo(["sysctl", f"net.ipv6.conf.{iface}.disable_ipv6={val}"])
            if result != 0:
                return result
        if val == "1":
            for iface in Path("/sys/class/net").iterdir():
                if iface.is_dir():
                    self._sudo(["ip", "-6", "addr", "flush", "dev", iface.name])
        conf = self.namedconf_dir / f"namedipv{'4' if ipv4 else '6'}.conf"
        self._sudo(["cp", str(conf), "/etc/named.conf"])
        self._sudo(["systemctl", "restart", "named"])

    def connect_vpn(self, choice: str) -> None:
        status = self._sudo(["wg", "show"]).stdout
        for line in status.splitlines():
            if line.startswith("interface:"):
                iface = line.split(":", 1)[1].strip()
                self._run(["wg-quick", "down", iface])
        self._set_network(False)
        time.sleep(2)
        if choice != "Disconnect":
            ok = self._run(["wg-quick", "up", choice]).returncode == 0
            self._set_network(ok)

    def main_menu(self) -> None:
        options = ["Wi-Fi Manager", "VPN Menu", "Change Wi-Fi Backend", "Cancel"]
        choice = self.fuzzel_menu(options)
        if choice == "Wi-Fi Manager":
            procs_dict = {p.name() for p in psutil.process_iter(attrs=["name"])}
            if "NetworkManager" in procs_dict:
                self._ui(["kitty", "nmtui"])
            elif "iwd" in procs_dict:
                self._ui(["kitty", "impala"])
            else:
                log.warning("No Wi-Fi backend running")
        elif choice == "VPN Menu":
            vpn_name = sys.argv[1] if len(sys.argv) > 1 else None
            if not vpn_name:
                lines = self.vpn_list.read_text().splitlines() + [
                    "─────",
                    "Disconnect",
                    "Cancel",
                ]
                vpn_name = self.fuzzel_menu(lines)
            if vpn_name and vpn_name != "Cancel":
                self.connect_vpn(vpn_name)
        elif choice == "Change Wi-Fi Backend":
            self.reset_wifi()
        elif choice in ("Cancel", ""):
            sys.exit(0)


if __name__ == "__main__":
    NetworkManager().main_menu()
