#!/usr/bin/env python3
"""
toggle_kanshi_hz.py

Toggles the refresh rate in the 'undocked' profile of
~/Lit/polka/config/kanshi/config between 60Hz and 144Hz,
then restarts the user kanshi.service to apply changes.
"""

from pathlib import Path
import subprocess
import re

KANSHI_CONFIG = Path.home() / "Lit/polka/config/kanshi/config"


def toggle_hz():
    if not KANSHI_CONFIG.exists():
        print(f"{KANSHI_CONFIG} does not exist!")
        return

    text = KANSHI_CONFIG.read_text()

    # Function to toggle Hz
    def replace_hz(match):
        current_hz = match.group(1)
        new_hz = "144" if current_hz == "60" else "60"
        return f"mode 1920x1080@{new_hz}Hz"

    # Split by profile blocks
    profile_blocks = re.split(r"(profile\s+\w+\s*{)", text)
    new_text = ""
    i = 0
    while i < len(profile_blocks):
        if profile_blocks[i].startswith("profile"):
            profile_header = profile_blocks[i]
            profile_body = (
                profile_blocks[i + 1] if (i + 1) < len(profile_blocks) else ""
            )
            full_profile = profile_header + profile_body

            if "undocked" in profile_header:
                # Replace mode line inside undocked profile
                full_profile = re.sub(
                    r"mode\s+1920x1080@(\d+)Hz", replace_hz, full_profile
                )

            new_text += full_profile
            i += 2
        else:
            new_text += profile_blocks[i]
            i += 1

    KANSHI_CONFIG.write_text(new_text)
    print(f"Toggled refresh rate in {KANSHI_CONFIG}")

    # Restart user kanshi.service to apply changes
    try:
        subprocess.run(["systemctl", "--user", "restart", "kanshi.service"], check=True)
        print("kanshi.service restarted successfully.")
    except Exception as e:
        print(f"Failed to restart kanshi.service: {e}")


if __name__ == "__main__":
    toggle_hz()
