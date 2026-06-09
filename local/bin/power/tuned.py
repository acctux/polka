#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from pathlib import Path

KANSHI_CONFIG = Path.home() / ".config" / "kanshi" / "config"


def set_hz(kanshi_config: Path, target_hz: str) -> None:
    def replace_mode(match):
        header, body, footer = match.group(1), match.group(2), match.group(3)
        updated_body = re.sub(
            r"mode\s+1920x1200@\d+Hz", f"mode 1920x1200@{target_hz}Hz", body
        )
        return f"{header}{updated_body}{footer}"

    if not kanshi_config.exists():
        print(f"Error: {kanshi_config} does not exist!", file=sys.stderr)
        return
    content = kanshi_config.read_text()
    pattern = r"(profile\s+undocked\s*\{)([^}]+)(\})"
    if not re.search(pattern, content):
        print("Warning: 'undocked' profile not found in kanshi config.")
        return
    new_content = re.sub(pattern, replace_mode, content, flags=re.DOTALL)
    kanshi_config.write_text(new_content)
    print(f"Set refresh rate to {target_hz}Hz in {kanshi_config}")
    try:
        cmd = ["systemctl", "--user", "restart", "kanshi.service"]
        subprocess.run(cmd, check=True)
        print("kanshi.service restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart kanshi.service: {e}", file=sys.stderr)


def set_profile(profile: str) -> None:
    try:
        cmd = ["tuned-adm", "profile", profile]
        subprocess.run(cmd, check=True)
        print(f"Switched tuned profile to '{profile}'")
    except subprocess.CalledProcessError as e:
        print(f"Failed to switch tuned profile: {e}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Switch tuned profile and update refresh rate."
    )
    parser.add_argument("profile", help="The tuned profile to apply (e.g., powersave)")
    parser.add_argument("hz", help="The target refresh rate in Hz (e.g., 60, 120)")
    args = parser.parse_args()
    set_profile(args.profile)
    set_hz(KANSHI_CONFIG, args.hz)


if __name__ == "__main__":
    main()

