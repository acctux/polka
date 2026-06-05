#!/usr/bin/env python3
import psutil
import subprocess
import sys
import time
from pathlib import Path
import logging


#########################
# LOG
#########################
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.INFO: "\033[36m",
        logging.WARNING: "\033[93m",
        logging.ERROR: "\033[31m",
    }
    RESET = "\033[0m"
    NAME = "\033[93m"

    def format(self, record):
        name = f"{self.NAME}{record.name}{self.RESET}"
        msg = f"{self.COLORS.get(record.levelno, '')}{record.getMessage()}{self.RESET}"
        return f"{name}: {msg}"


def get_logger(log_name=None, level=logging.INFO):
    log = logging.getLogger(log_name)
    if log.handlers:
        return log
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(ColorFormatter())
    log.addHandler(handler)
    log.setLevel(level)
    log.propagate = False
    return log


log = get_logger("NetworkManager")


##############################
# Wi-Fi Manager
##############################
class WiFiManager:
    SERVICES = {
        "iwd.service": "NetworkManager.service",
        "NetworkManager.service": "iwd.service",
    }

    def __init__(self):
        self.driver = ""

    def run_cmd(self, cmd: list[str]) -> str:
        cmd = ["sudo", "-A"] + cmd
        try:
            result = subprocess.run(cmd, text=True, capture_output=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            log.error(f"Error running command {cmd}: {e.stderr.strip()}")
            return ""

    def reset_wifi(self) -> None:
        for current in self.SERVICES:
            status = self.run_cmd(["systemctl", "is-active", current])
            if status == "active":
                target = self.SERVICES[current]
                try:
                    result = subprocess.run(
                        [
                            "zenity",
                            "--question",
                            "--text",
                            f"{current} is running. Switch to {target}?",
                        ],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode != 0:
                        log.info("Wi-Fi reset aborted by user.")
                        return
                except subprocess.CalledProcessError:
                    log.error("Zenity dialog failed.")
                    return
                log.info(f"Switching from {current} to {target}...")
                self.run_cmd(["systemctl", "stop", current])
                self.run_cmd(["systemctl", "disable", current])
                if self.driver:
                    log.info(f"Reloading driver {self.driver}...")
                    self.run_cmd(["modprobe", "-r", self.driver])
                    self.run_cmd(["modprobe", self.driver])
                    time.sleep(5)
                self.run_cmd(["systemctl", "enable", "--now", target])
                log.info(f"Switched from {current} to {target} successfully.")
                return
        log.info("Neither iwd nor NetworkManager is active. No changes made.")


##############################
# VPN Manager
##############################
class VPNManager:
    def __init__(
        self,
        fuzzel_config=Path.home() / ".config/fuzzel/fav-menu.ini",
        namedconf_dir=Path(__file__).resolve().parent / "namedconf",
        vpn_list=Path("/var/cache/mysysinfo/vpn.list"),
    ):
        self.namedconf_dir = namedconf_dir
        self.fuzzel_config = fuzzel_config
        self.vpn_list = vpn_list

    def run_sudo(
        self, cmd: list[str], sudo: bool = True
    ) -> subprocess.CompletedProcess:
        if sudo:
            cmd = ["sudo", "-A"] + cmd
        log.info(f"Running {cmd}")
        return subprocess.run(cmd, text=True, capture_output=True)

    def run_fuzzel(self) -> str | None:
        vpn_lines = self.vpn_list.read_text().splitlines()
        menu_options = vpn_lines + ["─────", "Disconnect", "Cancel"]
        cmd = [
            "fuzzel",
            "--dmenu",
            f"--width={max(map(len, menu_options)) + 1}",
            "--lines",
            str(len(menu_options)),
            "--config",
            str(self.fuzzel_config),
            "--x-margin=80",
        ]
        choice = subprocess.run(
            cmd, input="\n".join(menu_options), text=True, capture_output=True
        ).stdout.strip()
        if choice in ("", "Cancel"):
            choice = None
        log.info(f"Selected: {choice}")
        return choice

    def set_network_and_named(self, ipv4: bool) -> None:
        named_conf_path = Path("/etc/named.conf")
        target_conf = self.namedconf_dir / f"namedipv{'4' if ipv4 else '6'}.conf"
        current_conf = self.run_sudo(["cat", str(named_conf_path)]).stdout
        if current_conf == target_conf.read_text():
            return
        time.sleep(1)
        self.run_sudo(["cp", str(target_conf), str(named_conf_path)])
        self.run_sudo(["systemctl", "restart", "named"])

    def disconnect_all_wg(self) -> None:
        wg_status = self.run_sudo(["wg", "show"]).stdout.splitlines()
        for line in wg_status:
            if line.startswith("interface:"):
                iface = line.split(":", 1)[1].strip()
                self.run_sudo(["wg-quick", "down", iface], sudo=False)
                time.sleep(0.5)

    def connect_vpn(self, choice: str) -> None:
        self.disconnect_all_wg()
        self.set_network_and_named(ipv4=False)
        time.sleep(1.5)
        if choice != "Disconnect":
            success = (
                self.run_sudo(["wg-quick", "up", choice], sudo=False).returncode == 0
            )
            self.set_network_and_named(ipv4=success)


def launch_wifi() -> None:
    try:
        process_names = []
        for p in psutil.process_iter(attrs=["name"]):
            process_names.append(p.name())
        if "NetworkManager" in process_names:
            subprocess.run(["kitty", "nmtui"])
            return
        elif "iwd" in process_names:
            subprocess.run(["kitty", "impala"])
            return
        else:
            log.warning("Neither NetworkManager nor iwd is running.")
    except Exception as e:
        log.error(f"Failed to launch WiFi Manager: {e}")


##############################
# Main Menu
##############################
def main_menu():
    options = [
        ("Wi-Fi Manager", "wifi"),
        ("VPN Menu", "vpn"),
        ("Change Wi-Fi Backend", "wifi_reset"),
        ("Cancel", "exit"),
    ]
    menu_text = [o[0] for o in options]
    width = max(map(len, menu_text)) + 1
    choice = subprocess.run(
        [
            "fuzzel",
            "--dmenu",
            f"--width={width}",
            "--lines",
            str(len(menu_text)),
            "--config",
            str(Path.home() / ".config/fuzzel/fav-menu.ini"),
        ],
        input="\n".join(menu_text),
        text=True,
        capture_output=True,
    ).stdout.strip()
    action = next((a[1] for a in options if a[0] == choice), None)
    if action == "wifi":
        launch_wifi()
    elif action == "vpn":
        cli_choice = sys.argv[1] if len(sys.argv) > 1 else None
        vpn = VPNManager()
        if not cli_choice:
            cli_choice = vpn.run_fuzzel()
            log.info(cli_choice)
        if cli_choice:
            vpn.connect_vpn(cli_choice)
    elif action == "wifi_reset":
        wifi = WiFiManager()
        wifi.reset_wifi()
    elif action == "exit" or action is None:
        sys.exit(0)


if __name__ == "__main__":
    main_menu()
