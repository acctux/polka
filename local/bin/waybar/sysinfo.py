#!/usr/bin/env python3

from pathlib import Path
import json

FILE = Path("/var/cache/mysysinfo/sysinfo.txt")


def main(sysinfo_file: Path):
    if not sysinfo_file.is_file():
        print(json.dumps({"text": "󰌢", "tooltip": "sysinfo unavailable"}))
        return
    data = {}
    with sysinfo_file.open() as f:
        for line in f:
            if ":" in line:
                key, value = line.rstrip("\n").split(":", 1)
                data[key.strip()] = value.strip()
    family = data.get("Manufacturer", "")
    tooltip = "\n".join(f"{key}: {value}\t" for key, value in data.items())
    print(json.dumps({"text": f"󰌢 {family}", "tooltip": tooltip}))


if __name__ == "__main__":
    main(FILE)
