#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path

LAYOUT_ICONS = {
    "English (US)": "🇺🇸",
    "Russian": "🇷🇺",
    "Russian (phonetic)": "🇷🇺",
    "Ukrainian": "🇺🇦",
}
KEYBOARD_NAME = "at-translated-set-2-keyboard"


def get_active_layout(keyboard_name: str) -> str:
    cmd = ["hyprctl", "devices", "-j"]
    devices = json.loads(subprocess.check_output(cmd, text=True))
    for keyboard in devices.get("keyboards", []):
        if keyboard.get("name") == keyboard_name:
            return keyboard.get("active_keymap", "")
    return ""


def main():
    cache_file = Path.home() / ".cache" / "keyboard_waybar" / "kb_cache.json"
    layout = get_active_layout(KEYBOARD_NAME)
    if layout in LAYOUT_ICONS:
        icon = LAYOUT_ICONS[layout]
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        layout_dict = {"layout": layout, "icon": icon}
        cache_file.write_text(json.dumps(layout_dict, ensure_ascii=False))
    else:
        cache = json.loads(cache_file.read_text())
        icon = cache.get("icon", "❓")
        layout = cache.get("layout", "Unknown")
    way_dict = {
        "text": icon,
        "tooltip": f"Layout: {layout}\t",
    }
    print(json.dumps(way_dict, ensure_ascii=False))


if __name__ == "__main__":
    main()
