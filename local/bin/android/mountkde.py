#!/usr/bin/env python3
import subprocess
import sys
import time
from pathlib import Path
import os
import shutil
import re

PHONE_PATH = Path.home() / "Phone"
ANDROID_MOUNT = PHONE_PATH / "Internal"
SD_MOUNT = PHONE_PATH / "SD"
SSH_KEY = Path.home() / ".config/kdeconnect/privateKey.pem"
ANDROID_USER = "kdeconnect"
ANDROID_DIR = "/storage/emulated/0"
SD_DIR = "/storage/0000-0000"
PHONE_ICON = "/usr/share/icons/WhiteSur-dark/places/scalable/folder-android.svg"


def run(cmd, check=False):
    result = subprocess.run(
        cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result.stdout.strip()


def select_device():
    output = run("kdeconnect-cli -l")
    if output:
        devices = re.findall(r"- .*?: ([a-f0-9]{8,})", output, re.I)
        if not devices:
            sys.exit("No KDE Connect devices found.")
        if len(devices) == 1:
            return devices[0]
        for i, d in enumerate(devices, 1):
            print(f"{i}: {d}")
        try:
            return devices[int(input("Select device: ")) - 1]
        except (ValueError, IndexError):
            sys.exit("Invalid selection.")


def activate_sftp(device_id):
    cmd = f"dbus-send --session --dest=org.kde.kdeconnect --print-reply /modules/kdeconnect/devices/{device_id}/sftp org.kde.kdeconnect.device.sftp.mountAndWait"
    run(cmd, True)


def detect_host(device_id):
    time.sleep(3)
    lines = run("mount")
    if lines:
        for line in lines.splitlines():
            if device_id in line and "kdeconnect" in line:
                match = re.search(r"kdeconnect@([0-9.]+)", line)
                if match:
                    return match.group(1)
        sys.exit("Failed to detect KDE Connect mount.")


def get_ssh_port(host):
    lines = run("ss -tnp")
    if lines:
        for line in lines.splitlines():
            if host in line and "ssh" in line:
                return line.split()[4].split(":")[-1]
        sys.exit("Failed to detect SSH port.")


def set_phone_icon(icon_path):
    icon_path = Path(icon_path).resolve()
    PHONE_PATH.mkdir(parents=True, exist_ok=True)
    if not icon_path.exists():
        print(f"Icon not found: {icon_path}")
        return
    try:
        run(f"gio set {PHONE_PATH} metadata::custom-icon file://{icon_path}")
        print(f"Custom icon set for {PHONE_PATH}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to set icon for {PHONE_PATH}: {e.stderr}")


def mount_storage(host, port):
    ANDROID_MOUNT.mkdir(parents=True, exist_ok=True)
    SD_MOUNT.mkdir(parents=True, exist_ok=True)
    opts = f"rw,nosuid,nodev,IdentityFile={SSH_KEY},port={port},uid={os.getuid()},gid={os.getgid()},allow_other"
    for remote, mount_point in [(ANDROID_DIR, ANDROID_MOUNT), (SD_DIR, SD_MOUNT)]:
        try:
            cmd = f"sshfs -o {opts} {ANDROID_USER}@{host}:{remote} {mount_point}"
            run(cmd, check=True)
        except subprocess.CalledProcessError:
            print(f"Failed to mount {mount_point}", file=sys.stderr)


def unmount_storage():
    for mp in [ANDROID_MOUNT, SD_MOUNT]:
        if mp.is_mount():
            try:
                run(f"fusermount3 -u {mp}", check=True)
                print(f"Unmounted {mp}")
            except subprocess.CalledProcessError:
                print(f"Failed to unmount {mp}", file=sys.stderr)
    if PHONE_PATH.exists() and PHONE_PATH.is_dir():
        try:
            shutil.rmtree(PHONE_PATH)
            print(f"Removed {PHONE_PATH}")
        except Exception as e:
            print(f"Failed to remove {PHONE_PATH}: {e}", file=sys.stderr)


def mount_kde():
    if ANDROID_MOUNT.is_mount():
        unmount_storage()
        return
    device_id = select_device()
    print(f"found {device_id}")
    activate_sftp(device_id)
    host = detect_host(device_id)
    port = get_ssh_port(host)
    set_phone_icon(PHONE_ICON)
    mount_storage(host, port)
    print(f"Mounted {device_id} at {ANDROID_MOUNT} and {SD_MOUNT}")


if __name__ == "__main__":
    mount_kde()
