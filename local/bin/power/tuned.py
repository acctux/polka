#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
import tomlkit


def run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed: {e}", file=sys.stderr)


def set_hz(config_path: Path, target_hz: str) -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        data = tomlkit.load(f)
    for profile in data.get("profile", []):
        if profile.get("name") == "undocked":
            for output in profile.get("output", []):
                if "1920x1200" in str(output.get("mode", "")):
                    output["mode"] = f"1920x1200@{target_hz}Hz"
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(data))
    run(["shikanectl", "reload"])


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: ./script.py <profile> <hz>")
        sys.exit(1)
    profile_arg = sys.argv[1]
    hz_arg = sys.argv[2]
    run(["tuned-adm", "profile", profile_arg])
    conf = Path.home() / ".config" / "shikane" / "config.toml"
    set_hz(conf, hz_arg)


if __name__ == "__main__":
    main()
