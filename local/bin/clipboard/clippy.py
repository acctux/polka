#!/usr/bin/env python3
from pathlib import Path
import subprocess

CONF_PATH = Path.home() / ".config" / "fuzzel" / "clipboard.ini"
MAX_WIDTH = 44
MAX_ENTRIES = 27


def run_cmd(
    cmd: list[str],
    check: bool,
    input_text: str | None = None,
) -> str:
    try:
        out = subprocess.run(
            cmd,
            input=input_text,
            text=True,
            capture_output=True,
            check=check,
        )
        return out.stdout.strip()
    except subprocess.CalledProcessError as e:
        if check:
            print(f"Error running {' '.join(cmd)}: {e.stderr}")
        return ""


def run_fuzz(
    menu_map: dict[str, str], max_w=MAX_WIDTH, clear_option="Clear History"
) -> None:
    lengths = [len(txt) for txt in menu_map]
    menu_width = min(max_w, max(lengths))
    separator = "—" * (menu_width)
    options = [clear_option, separator] + list(menu_map.keys())
    fuzzel_cmd = [
        "fuzzel",
        "--dmenu",
        f"--config={CONF_PATH}",
        f"--lines={len(options)}",
        f"--width={menu_width}",
        "--x-margin=10",
    ]
    input_data = "\n".join(options)
    selection = run_cmd(fuzzel_cmd, check=False, input_text=input_data)
    if not selection or selection == separator:
        return
    elif selection == clear_option:
        run_cmd(["cliphist", "wipe"], check=False)
        return
    if line := menu_map.get(selection):
        decoded = run_cmd(["cliphist", "decode"], check=True, input_text=line)
        if decoded:
            run_cmd(["wl-copy"], check=True, input_text=decoded)


def get_menu_map(max_entries: int = MAX_ENTRIES) -> dict[str, str]:
    raw_output = run_cmd(["cliphist", "list"], check=True)
    menu_map = {}
    for line in raw_output.splitlines()[:max_entries]:
        parts = line.split(maxsplit=1)
        display_text = parts[1] if len(parts) > 1 else parts[0]
        menu_map[display_text] = line
    return menu_map


if __name__ == "__main__":
    menu_map = get_menu_map()
    run_fuzz(menu_map)

