#!/usr/bin/env python3

import json
import re
import subprocess

RATE = re.compile(r"@\s*([\d.]+\s+\S+/s)")


def parse_downloads(output: str) -> list[tuple[str, str, str, str]]:
    downloads = []
    pending = None

    for line in output.splitlines():
        line = line.strip()

        if line.startswith(("[D]", "[P]")):
            details = line.split("]", 1)[1].split()
            if len(details) >= 3:
                percent = details[0]
                name = " ".join(details[1:-1])
                if len(name) > 35:
                    name = name[:32] + "..."
                pending = (name, percent)

        elif line.startswith("["):
            pending = None

        elif pending and "ETA:" in line:
            eta = line.partition("ETA:")[2].strip()
            if eta == "-":
                eta = "Paused"
            match = RATE.search(line)
            rate = match.group(1) if match else ""
            name, percent = pending
            downloads.append((name, percent, eta, rate))
            pending = None

    return downloads


def print_bar(text: str = "", tooltip: str = "", way_class: str = "") -> None:
    print(json.dumps({"text": text, "tooltip": tooltip, "class": way_class}))


def main() -> None:
    service = subprocess.run(
        ["systemctl", "--user", "is-active", "deluged"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=1,
        check=False,
    ).returncode

    if service != 0:
        print_bar()
        return

    result = subprocess.run(
        ["deluge-console", "info"],
        capture_output=True,
        timeout=3,
        check=False,
    )
    downloads = parse_downloads(result.stdout.decode())

    if not downloads:
        print_bar("", "No active downloads\t", "idle")
        return
    downs = []
    way_class = ""
    for name, percent, eta, rate in downloads:
        line = f"{name}\t\n%: {percent}\nETA: {eta}"
        if rate:
            way_class = "downloading"
            line = line + f"\nRate: {rate}"
        downs.append(line)

    tooltip = "\n────────────────────────────────────\n".join(downs)
    print_bar("", tooltip, way_class)


if __name__ == "__main__":
    main()
