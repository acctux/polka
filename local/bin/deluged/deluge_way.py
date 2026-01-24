#!/usr/bin/env python3
import json
import os
import re
import subprocess

MAX_LEN = 30


def run(cmd, timeout=3):
    try:
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONWARNINGS": "ignore"},
        ).stdout
    except Exception:
        return ""


def trim(s):
    return s if len(s) <= MAX_LEN else s[: MAX_LEN - 1] + "…"


def parse_downloads(text):
    downloads = []
    name = None
    for line in text.splitlines():
        if line.startswith("["):
            raw = line.split("]", 1)[1].strip()
            name = trim(re.sub(r"\s+[a-fA-F0-9]{40}$", "", raw))
        elif name and "ETA:" in line:
            eta = line.split("ETA:", 1)[1].strip()
            if eta != "-":
                downloads.append((name, eta))
            name = None
    return downloads


def main():
    cmd = ["systemctl", "--user", "is-active", "deluged"]
    if run(cmd, 1).strip() != "active":
        print(json.dumps({"text": ""}))
        return
    downloads = parse_downloads(run(["deluge-console", "info"]))
    print(
        json.dumps(
            {
                "text": "",
                "tooltip": (
                    "\n".join(f"{n}\nETA: {e}" for n, e in downloads)
                    if downloads
                    else "No active downloads"
                ),
                "class": "downloading" if downloads else "idle",
            }
        )
    )


if __name__ == "__main__":
    main()

