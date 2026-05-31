#!/usr/bin/env python3

import json
import subprocess

LAYOUT_ICONS = {
    "English (US)": "🇺🇸",
    "Russian": "🇷🇺",
    "Ukrainian": "🇺🇦",
}
devices = subprocess.check_output(["hyprctl", "devices", "-j"], text=True)
data = json.loads(devices)
keyboards = {kb["name"]: kb for kb in data["keyboards"]}
layout = keyboards.get("at-translated-set-2-keyboard", {}).get("active_keymap")
print(LAYOUT_ICONS.get(layout, "❓"))
