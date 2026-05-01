#!/usr/bin/env python3

import logging
import sys
import subprocess
import time


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


log = get_logger("WiFiReset")


def run_cmd(cmd, sudo=False) -> str:
    if sudo:
        cmd = ["sudo", "-A"] + cmd
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log.error(f"Error running command: {e.stderr.strip()}")
        return ""


def zenity_dialog(message) -> bool:
    try:
        result = subprocess.run(
            ["zenity", "--question", "--text", message], capture_output=True, text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        log.error("Error running Zenity dialog.")
        return False


def check_service_status(service_name) -> bool:
    try:
        result = run_cmd(["systemctl", "is-active", service_name])
        if result == "active":
            return True
        log.warning(
            f"{service_name} is {'inactive' if result != 'active' else 'unknown'}."
        )
    except subprocess.CalledProcessError as e:
        log.warning(f"Service {service_name} not found or error: {e.stderr.strip()}")
    return False


def find_wifi_driver() -> str:
    result = run_cmd(["lspci", "-k"], sudo=False)
    if result:
        log.debug(f"Full lspci output:\n{result}")
        lines = result.splitlines()
        for i, line in enumerate(lines):
            if "Network controller" in line:
                log.debug(f"Found network controller line: {line}")
                for next_line in lines[i + 1 :]:
                    if "Kernel driver in use" in next_line:
                        driver = next_line.split(":")[1].strip()  # Extract driver
                        log.info(f"Detected Wi-Fi driver: {driver}")
                        return driver
        log.warning("Could not detect Wi-Fi driver.")
    return ""


def reset_wifi_services():
    try:
        driver = find_wifi_driver()
        if not driver:
            log.error("Wi-Fi driver could not be found. Aborting Wi-Fi reset.")
            return

        if check_service_status("iwd.service"):
            if not zenity_dialog("IWD is running. Set to NetworkManager?"):
                log.info("Wi-Fi reset aborted by user.")
                return
            run_cmd(["systemctl", "stop", "iwd.service"], sudo=True)
            run_cmd(["systemctl", "disable", "iwd.service"], sudo=True)
            time.sleep(2)
            log.info(f"Unloading and reloading {driver}...")
            run_cmd(["modprobe", "-r", driver], sudo=True)
            run_cmd(["modprobe", driver], sudo=True)
            log.info("Waiting for 5 seconds before starting NetworkManager...")
            time.sleep(5)
            log.info("Enabling and starting NetworkManager.service.")
            run_cmd(["systemctl", "start", "NetworkManager.service"], sudo=True)
            run_cmd(["systemctl", "enable", "NetworkManager.service"], sudo=True)
        elif check_service_status("NetworkManager.service"):
            if not zenity_dialog("NetworkManager is running. Set to IWD?"):
                log.info("Wi-Fi reset aborted by user.")
                return
            run_cmd(["systemctl", "stop", "NetworkManager.service"], sudo=True)
            run_cmd(["systemctl", "disable", "NetworkManager.service"], sudo=True)
            log.info("Enabling and starting iwd.service...")
            run_cmd(["systemctl", "enable", "--now", "iwd.service"], sudo=True)
        else:
            log.info("Neither iwd nor NetworkManager active.")
        log.info("Wi-Fi services have been reset successfully.")
    except Exception as e:
        log.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    reset_wifi_services()
