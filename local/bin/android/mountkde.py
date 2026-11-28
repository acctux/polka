#!/usr/bin/env python3

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PHONE_PATH = Path.home() / "Phone"
MOUNTS = {
    "/storage/emulated/0": PHONE_PATH / "Internal",
    "/storage/0000-0000": PHONE_PATH / "SD",
}
SSH_KEY = Path.home() / ".config" / "kdeconnect" / "privateKey.pem"
PHONE_ICON = Path("/usr/share/icons/WhiteSur-dark/places/scalable/folder-android.svg")


def select_device():
    result = subprocess.run(
        ["kdeconnect-cli", "-l"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    if not result:
        sys.exit("No KDE Connect devices found.")

    devices = re.findall(r"- .*?: ([a-f0-9]{8,})", result, re.IGNORECASE)
    if not devices:
        sys.exit("No KDE Connect devices found.")
    if len(devices) == 1:
        return devices[0]
    else:
        return devices


def activate_sftp(device_id):
    subprocess.run(
        [
            "dbus-send",
            "--session",
            "--dest=org.kde.kdeconnect",
            "--print-reply",
            f"/modules/kdeconnect/devices/{device_id}/sftp",
            "org.kde.kdeconnect.device.sftp.mountAndWait",
        ],
        check=True,
    )


def detect_host(device_id):
    time.sleep(3)
    result = subprocess.run(
        ["mount"],
        text=True,
        check=False,
        capture_output=True,
    )

    for line in result.stdout.splitlines():
        if device_id in line and "kdeconnect" in line:
            match = re.search(r"kdeconnect@([0-9.]+)", line)
            if match:
                return match.group(1)

    sys.exit("Failed to detect KDE Connect mount.")


def get_ssh_port(host):
    result = subprocess.run(
        ["ss", "-tnp"],
        text=True,
        capture_output=True,
        check=False,
    )

    for line in result.stdout.splitlines():
        if host in line and "ssh" in line:
            return line.split()[4].rsplit(":", 1)[-1]

    sys.exit("Failed to detect SSH port.")


def set_phone_icon():
    PHONE_PATH.mkdir(parents=True, exist_ok=True)
    if not PHONE_ICON.exists():
        print(f"Icon not found: {PHONE_ICON}")
        return

    result = subprocess.run(
        [
            "gio",
            "set",
            str(PHONE_PATH),
            "metadata::custom-icon",
            PHONE_ICON.as_uri(),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        print(f"Failed to set icon: {result.stderr}", file=sys.stderr)
    else:
        print(f"Custom icon set for {PHONE_PATH}")


def mount_storage(host, port):
    options = (
        f"rw,nosuid,nodev,IdentityFile={SSH_KEY},port={port},"
        f"uid={os.getuid()},gid={os.getgid()},allow_other"
    )

    for remote, mount_point in MOUNTS.items():
        mount_point.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                "sshfs",
                "-o",
                options,
                f"kdeconnect@{host}:{remote}",
                str(mount_point),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            print(f"Failed to mount {mount_point}", file=sys.stderr)


def unmount_storage():
    for mount_point in MOUNTS.values():
        if mount_point.is_mount():
            result = subprocess.run(
                [
                    "fusermount3",
                    "-u",
                    str(mount_point),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode:
                print(f"Failed to unmount {mount_point}", file=sys.stderr)
            else:
                print(f"Unmounted {mount_point}")

    if any(mount_point.is_mount() for mount_point in MOUNTS.values()):
        print("Not removing Phone: a mount point is still mounted.", file=sys.stderr)
        return

    try:
        if not all(not any(mount_point.iterdir()) for mount_point in MOUNTS.values()):
            print("Not removing Phone: a mount point is not empty.", file=sys.stderr)
            return

        if PHONE_PATH.is_dir():
            shutil.rmtree(PHONE_PATH)
            print(f"Removed {PHONE_PATH}")
    except OSError as error:
        print(f"Could not check or remove {PHONE_PATH}: {error}", file=sys.stderr)


def main():
    internal_mount = MOUNTS["/storage/emulated/0"]
    if internal_mount.is_mount():
        unmount_storage()
        return

    device_id = select_device()
    print(f"Found {device_id}")

    activate_sftp(device_id)
    host = detect_host(device_id)
    port = get_ssh_port(host)
    set_phone_icon()
    mount_storage(host, port)

    print(f"Mounted {device_id} at {PHONE_PATH}")


if __name__ == "__main__":
    main()
