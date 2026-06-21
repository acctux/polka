#!/usr/bin/env python3
import json
import subprocess


def run(cmd, timeout=3):
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        ).stdout
    except Exception:
        return ""


def parse_downloads():
    downloads = []
    pending_name = None
    lines = run(["deluge-console", "info"]).splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith("["):
            raw = line.split("]", 1)[1].strip()
            pending_name = raw.rsplit(" ", 1)[0]
        elif pending_name and "ETA:" in line:
            eta = line.split("ETA:", 1)[1].strip()
            if eta != "-":
                downloads.append((pending_name, eta))
            pending_name = None
    return downloads


def print_bar(text: str = "", tooltip: str = "", way_class: str = ""):
    print(json.dumps({"text": text, "tooltip": tooltip, "class": way_class}))


def main():
    cmd = ["systemctl", "--user", "is-active", "deluged"]
    if run(cmd, 1).strip() != "active":
        print_bar()
        return
    downloads = parse_downloads()
    tooltip = "No active downloads"
    way_class = "idle"
    if downloads:
        lines = []
        for name, eta in downloads:
            lines.append(f"{name}\t\nETA: {eta}")
        tooltip = "\n".join(lines)
        way_class = "downloading"
    print_bar("", tooltip, way_class)


if __name__ == "__main__":
    main()
