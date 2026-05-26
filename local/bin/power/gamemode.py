#!/usr/bin/env python3

import subprocess

SERVICES = ["kdeconnectd", "swaync", "waybar", "swww-daemon", "hypridle"]


def service_running(service: str) -> bool:
    result = subprocess.run(
        ["systemctl", "--user", "is-active", service], capture_output=True, text=True
    )
    return result.stdout.strip() == "active"


def start_service(service: str) -> None:
    subprocess.run(
        ["systemctl", "--user", "start", service],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"Started: {service}")


def stop_service(service: str) -> None:
    subprocess.run(
        ["systemctl", "--user", "stop", service],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"Stopped: {service}")


def get_running_services() -> list[str]:
    return [service for service in SERVICES if service_running(service)]


def toggle_services(services: list[str] = SERVICES) -> None:
    running_services = get_running_services()
    running_count = len(running_services)
    stopped_count = len(services) - running_count
    print(f"Running: {running_count}")
    print(f"Stopped: {stopped_count}\n")
    should_stop = running_count > stopped_count
    if should_stop:
        print("Majority are running.")
        print("Stopping all managed user services...\n")
        for service in services:
            stop_service(service)
        print("\nAll services stopped.")
    else:
        print("Majority are stopped (or tied).")
        print("Starting all managed user services...\n")
        for service in services:
            start_service(service)
        print("\nAll services started.")


if __name__ == "__main__":
    toggle_services()

