#!/usr/bin/env python3

import subprocess
from pathlib import Path

CONF_PATH = Path.home() / ".config" / "fuzzel" / "clipboard.ini"
MAX_WIDTH = 44
MAX_ENTRIES = 27


def run_cmd(
    cmd: list[str],
    check: bool,
    input_text: str | None,
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
    menu_map: dict[str, str],
    fuzz_conf: Path = CONF_PATH,
    max_entries: int = MAX_ENTRIES,
    max_w: int = MAX_WIDTH,
    clear_option: str = "Clear History",
    xmargin: int = 10,
) -> None:
    lengths = [len(txt) for txt in menu_map]
    menu_width = min(max_w, max(lengths))
    separator = "—" * (menu_width)
    options = [clear_option, separator] + list(menu_map.keys())
    input_data = "\n".join(options)
    selection = run_cmd(
        [
            "fuzzel",
            "--dmenu",
            f"--config={fuzz_conf}",
            f"--lines={max_entries}",
            f"--width={menu_width}",
            f"--x-margin={xmargin}",
        ],
        check=False,
        input_text=input_data,
    )
    if not selection or selection == separator:
        return
    elif selection == clear_option:
        run_cmd(
            ["cliphist", "wipe"],
            check=False,
            input_text=None,
        )
        return
    if line := menu_map.get(selection):
        decoded = run_cmd(
            ["cliphist", "decode"],
            check=True,
            input_text=line,
        )
        if decoded:
            run_cmd(
                ["wl-copy"],
                check=True,
                input_text=decoded,
            )


def get_menu_map() -> dict[str, str]:
    raw_output = run_cmd(
        ["cliphist", "list"],
        check=True,
        input_text=None,
    )
    menu_map = {}
    for line in raw_output.splitlines():
        parts = line.split(maxsplit=1)
        display_text = parts[1] if len(parts) > 1 else parts[0]
        menu_map[display_text] = line
    return menu_map


if __name__ == "__main__":
    menu_map = get_menu_map()
    run_fuzz(menu_map)
