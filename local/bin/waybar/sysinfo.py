#!/usr/bin/env python3

from pathlib import Path
import json

FILE = Path("/var/cache/mysysinfo/sysinfo.txt")


def load_sysinfo(path: Path) -> dict:
    data = {}
    with path.open() as f:
        for line in f:
            if ":" in line:
                key, value = line.rstrip("\n").split(":", 1)
                data[key.strip()] = value.strip()
    return data


def build_tooltip(data: dict) -> str:
    return "\n".join(f"{k}: {v}\t" for k, v in data.items())


def main():
    if not FILE.is_file():
        print(json.dumps({"text": "󰌢", "tooltip": "sysinfo unavailable"}))
        return
    data = load_sysinfo(FILE)
    family = data.get("Manufacturer", "")
    print(json.dumps({"text": f"󰌢 {family}", "tooltip": build_tooltip(data)}))


if __name__ == "__main__":
    main()
