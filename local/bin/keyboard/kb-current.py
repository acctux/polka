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
CACHE_FILE = Path.home() / ".cache" / "keyboard_waybar" / "kb_cache.json"


def read_cache(cache_file: Path) -> dict:
    try:
        return json.loads(cache_file.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def write_cache(cache_file: Path, layout: str, icon: str) -> None:
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        layout_dict = {"layout": layout, "icon": icon}
        cache_file.write_text(json.dumps(layout_dict, ensure_ascii=False))
    except OSError:
        pass


def get_active_layout(keyboard_name: str) -> str:
    try:
        cmd = ["hyprctl", "devices", "-j"]
        devices = json.loads(subprocess.check_output(cmd, text=True))
    except subprocess.CalledProcessError:
        return ""
    for keyboard in devices.get("keyboards", []):
        if keyboard.get("name") == keyboard_name:
            return keyboard.get("active_keymap", "")
    return ""


def print_waybar(text: str, tooltip: str, waybar_class: str) -> None:
    data = {"text": text, "tooltip": tooltip, "class": waybar_class}
    print(json.dumps(data, ensure_ascii=False))


def main():
    layout = get_active_layout(KEYBOARD_NAME)
    cache = read_cache(CACHE_FILE)
    if layout in LAYOUT_ICONS:
        icon = LAYOUT_ICONS[layout]
        write_cache(CACHE_FILE, layout, icon)
    else:
        icon = cache.get("icon", "❓")
        layout = cache.get("layout", "Unknown")
    waybar_class = layout.lower().replace(" ", "-") if layout else "unknown"
    print_waybar(text=icon, tooltip=f"Layout: {layout}\t", waybar_class=waybar_class)


if __name__ == "__main__":
    main()
