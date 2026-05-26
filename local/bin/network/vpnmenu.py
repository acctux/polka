#!/usr/bin/env python3
import psutil
import subprocess
import sys
import time
from pathlib import Path
import logging


##############################
# Logging Setup
##############################
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[34m",  # Blue
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[41m",  # Red background
    }
    RESET = "\033[0m"
    UNDERLINE = "\033[4m"

    def format(self, record):
        message = f"{record.name}: {record.getMessage()}"
        color = self.COLORS.get(record.levelno, "")
        if color:
            message = f"{color}{message}{self.RESET}"
        if record.levelno == logging.CRITICAL:
            message = f"{self.UNDERLINE}{message}{self.RESET}"
        return message


def get_logger(log_name: str | None = None, level=logging.INFO):
    logger = logging.getLogger(log_name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(ColorFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


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

    def reset_wifi(self):
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
    vpn_list = Path("/var/cache/mysysinfo/vpn.list")

    def __init__(self):
        self.named_conf_path = Path("/etc/named.conf")
        self.namedconf_dir = Path(__file__).resolve().parent / "namedconf"
        self.fuzzel_config = Path.home() / ".config/fuzzel/fav-menu.ini"

    def run_sudo(
        self, cmd: list[str], sudo: bool = True
    ) -> subprocess.CompletedProcess:
        if sudo:
            cmd = ["sudo", "-A"] + cmd
        log.info(f"Running {cmd}")
        return subprocess.run(cmd, text=True, capture_output=True)

    def run_fuzzel(self) -> str | None:
        options = self.vpn_list.read_text().splitlines() + [
            "─────",
            "Disconnect",
            "Cancel",
        ]
        width = max(map(len, options)) + 1
        choice = subprocess.run(
            [
                "fuzzel",
                "--dmenu",
                f"--width={width}",
                "--lines",
                str(len(options)),
                "--config",
                str(self.fuzzel_config),
                "--x-margin=80",
            ],
            input="\n".join(options),
            text=True,
            capture_output=True,
        ).stdout.strip()
        log.info(choice)
        return None if choice in ("", "Cancel") else choice

    def set_network_and_named(self, ipv4: bool):
        val = "1" if ipv4 else "0"
        for key in ("all", "default"):
            self.run_sudo(["sysctl", "-w", f"net.ipv6.conf.{key}.disable_ipv6={val}"])
        target_conf = self.namedconf_dir / f"namedipv{'4' if ipv4 else '6'}.conf"
        current_conf = self.run_sudo(["cat", str(self.named_conf_path)]).stdout
        if current_conf == target_conf.read_text():
            return
        time.sleep(1)
        self.run_sudo(["cp", str(target_conf), str(self.named_conf_path)])
        self.run_sudo(["systemctl", "restart", "named"])

    def disconnect_all_wg(self):
        wg_status = self.run_sudo(["wg", "show"]).stdout.splitlines()
        for line in wg_status:
            if line.startswith("interface:"):
                iface = line.split(":", 1)[1].strip()
                self.run_sudo(["wg-quick", "down", iface], sudo=False)
                time.sleep(0.5)

    def connect_vpn(self, choice: str):
        self.disconnect_all_wg()
        self.set_network_and_named(ipv4=False)
        time.sleep(0.5)
        if choice != "Disconnect":
            success = (
                self.run_sudo(["wg-quick", "up", choice], sudo=False).returncode == 0
            )
            time.sleep(0.5)
            self.set_network_and_named(ipv4=success)


def launch_wifi():
    try:
        process_names = [p.name() for p in psutil.process_iter(attrs=["name"])]
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
    cli_choice = sys.argv[1] if len(sys.argv) > 1 else None
    options = [
        ("Launch Wi-Fi Manager", "wifi"),
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
        if not cli_choice:
            cli_choice = VPNManager().run_fuzzel()
            log.info(cli_choice)
        if cli_choice:
            VPNManager().connect_vpn(cli_choice)
    elif action == "wifi_reset":
        WiFiManager().reset_wifi()
    elif action == "exit" or action is None:
        sys.exit(0)


if __name__ == "__main__":
    main_menu()
