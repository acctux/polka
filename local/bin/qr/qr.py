#!/usr/bin/env python3
import logging
import re
import subprocess
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="\033[34m%(levelname)s: %(message)s\033[0m",
    stream=sys.stderr,
)
log = logging.getLogger("QR")


def handle_decoded(raw_payload: str) -> None:
    decoded = raw_payload.strip()
    if decoded.startswith("QR-Code:"):
        decoded = decoded.removeprefix("QR-Code:")

    if decoded.startswith(("http://", "https://")):
        log.info("Opening URL: %s", decoded)
        subprocess.run(["xdg-open", decoded], check=False)
    elif decoded.startswith("WIFI:"):
        connect_wifi(decoded)
    else:
        log.info("Copying: %s", decoded)
        subprocess.run(["wl-copy"], input=decoded, text=True, check=False)


def connect_wifi(decoded: str) -> None:
    ssid_match = re.search(r"(?:^WIFI:|;)S:([^;]*)(?:;|$)", decoded)
    pass_match = re.search(r"(?:^|;)P:([^;]*)(?:;|$)", decoded)

    if not ssid_match:
        log.error("Could not parse SSID.")
        return

    ssid = ssid_match.group(1)
    password = pass_match.group(1) if pass_match else None

    subprocess.run(["iwctl", "station", "wlan0", "scan"], check=False)
    time.sleep(4)

    cmd = ["iwctl", "station", "wlan0", "connect", ssid]
    if password:
        cmd.extend(["--passphrase", password])

    log.info("Connecting to %s via iwd...", ssid)
    subprocess.run(cmd, check=False)


def scan_camera() -> None:
    scanner = subprocess.Popen(
        ["zbarcam", "--raw"],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert scanner.stdout is not None
        for line in scanner.stdout:
            if line.strip():
                handle_decoded(line)
                break
    finally:
        if scanner.poll() is None:
            scanner.terminate()
            scanner.wait()


def scan_screen() -> None:
    selection = subprocess.run(["slurp"], capture_output=True, text=True, check=False)
    region = selection.stdout.strip()

    if selection.returncode != 0 or not region:
        log.info("Selection cancelled.")
        return

    grim = subprocess.Popen(["grim", "-g", region, "-"], stdout=subprocess.PIPE)
    try:
        if grim.stdout is None:
            log.error("Could not capture grim output.")
            return

        scanner = subprocess.Popen(
            ["zbarimg", "--quiet", "-"],
            stdin=grim.stdout,
            stdout=subprocess.PIPE,
            text=True,
        )
        grim.stdout.close()  # Let the scanner receive EOF when grim exits.

        stdout, _ = scanner.communicate()
        grim_status = grim.wait()

        if scanner.returncode != 0:
            log.warning("QR scanning failed (zbarimg exit %s).", scanner.returncode)
        elif grim_status != 0:
            log.warning("Screenshot capture failed (grim exit %s).", grim_status)
        elif stdout.strip():
            handle_decoded(stdout.strip())
        else:
            log.warning("No QR code found.")

    finally:
        if scanner is not None and scanner.poll() is None:
            scanner.terminate()
            scanner.wait()

        if grim.poll() is None:
            grim.terminate()
            grim.wait()


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "camera"

    if mode == "camera":
        scan_camera()
    elif mode == "screen":
        scan_screen()
    else:
        print(f"Usage: {sys.argv[0]} [camera|screen]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
