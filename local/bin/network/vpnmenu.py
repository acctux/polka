#!/usr/bin/env python3
import logging
import subprocess
import sys
import time
from pathlib import Path
import psutil


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
    fuzzel_config = Path.home() / ".config" / "fuzzel" / "waybar.ini"
    namedconf_dir = Path(__file__).resolve().parent / "namedconf"
    resolvconf_dir = Path(__file__).resolve().parent / "resolvconf"
    wifi_services = {
        "iwd.service": "NetworkManager.service",
        "NetworkManager.service": "iwd.service",
    }
    vpn_list = Path("/var/cache/mysysinfo/vpn.list")

    def _run(
        self, cmd: list[str], sudo: bool, input: str | None = None
    ) -> subprocess.CompletedProcess:
        if sudo:
            cmd = ["sudo", "-A"] + cmd
        log.info(f"Running {cmd}")
        return subprocess.run(cmd, text=True, capture_output=True, input=input)

    def fuzzel_menu(self, options: list[str]) -> str:
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
        return self._run(cmd, False, input=menu_text).stdout.strip()

    def reset_wifi(self) -> None:
        for current, target in self.wifi_services.items():
            cmd = ["systemctl", "is-active", current]
            if self._run(cmd, False).stdout.strip() != "active":
                continue
            cmd = [
                "zenity",
                "--question",
                "--text",
                f"{current} running. Switch to {target}?",
            ]
            if self._run(cmd, False).returncode != 0:
                log.info("Wi-Fi reset aborted by user.")
                return
            log.info(f"Switching from {current} to {target}...")
            self._run(["systemctl", "stop", current], True)
            self._run(["modprobe", "-r", "rtw89_8852be"], True)
            time.sleep(1)
            self._run(["modprobe", "rtw89_8852be"], True)
            time.sleep(10)
            self._run(["systemctl", "start", target], True)
            log.info(f"Switched from {current} to {target} successfully.")
            return
        log.info("Neither iwd nor NetworkManager is active. No changes made.")

    # --- VPN ---
    def set_network(self, ipv4: bool) -> None:
        val = "1" if ipv4 else "0"
        for iface in ["all", "default", "lo"]:
            self._run(["sysctl", f"net.ipv6.conf.{iface}.disable_ipv6={val}"], True)
        if ipv4:
            interfaces = []
            net_dir = Path("/sys/class/net")
            for iface in net_dir.iterdir():
                if iface.is_dir():
                    interfaces.append(iface.name)
            for name in interfaces:
                self._run(["ip", "-6", "addr", "flush", "dev", name], True)
        target_conf = self.resolvconf_dir / f"resolvconf{'4' if ipv4 else '6'}.conf"
        print(target_conf)
        self._run(["cp", str(target_conf), "/etc/resolvconf.conf"], True)
        time.sleep(0.5)
        self._run(["resolvconf", "-u"], True)
        self._run(["systemctl", "stop" if ipv4 else "start", "named"], True)

    def connect_vpn(self, choice: str) -> None:
        status = self._run(["wg", "show"], True).stdout
        for line in status.splitlines():
            if line.startswith("interface:"):
                iface = line.split(":", 1)[1].strip()
                self._run(["wg-quick", "down", iface], sudo=False)
        self.set_network(ipv4=False)
        time.sleep(1)
        if choice != "Disconnect":
            ipv4 = True
            if self._run(["wg-quick", "up", choice], sudo=False).returncode != 0:
                ipv4 = False
            self.set_network(ipv4=ipv4)

    def main_menu(self) -> None:
        options = ["Wi-Fi Manager", "VPN Menu", "Change Wi-Fi Backend", "Cancel"]
        choice = self.fuzzel_menu(options)
        if choice == "Wi-Fi Manager":
            procs_dict = {p.name() for p in psutil.process_iter(attrs=["name"])}
            if "NetworkManager" in procs_dict:
                self._run(["kitty", "nmtui"], True)
            elif "iwd" in procs_dict:
                self._run(["kitty", "impala"], True)
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
