#!/usr/bin/env python3
from pathlib import Path
import subprocess

CONFIG_PATH = Path.home() / ".config" / "fuzzel" / "clipboard.ini"
MAX_WIDTH = 44
MAX_ENTRIES = 27
CLEAR_OPTION = "Clear History"


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


def handle_selection(
    selection: str,
    separator: str,
    menu_map: dict[str, str],
    clear_option: str,
) -> None:
    if not selection or selection == separator:
        return
    if selection == clear_option:
        run_cmd(
            ["cliphist", "wipe"],
            check=False,
        )
        return
    if original_line := menu_map.get(selection):
        decoded_content = run_cmd(
            ["cliphist", "decode"],
            check=True,
            input_text=original_line,
        )
        if decoded_content:
            run_cmd(
                ["wl-copy"],
                check=True,
                input_text=decoded_content,
            )


def clipboard_fuzzel_menu(
    config_path: Path = CONFIG_PATH,
    max_width: int = MAX_WIDTH,
    max_entries: int = MAX_ENTRIES,
    clear_option=CLEAR_OPTION,
) -> None:
    raw_output = run_cmd(["cliphist", "list"], check=True)
    if not raw_output:
        return
    menu_map = {}
    for line in raw_output.splitlines()[:max_entries]:
        if parts := line.split(maxsplit=1):
            display_text = parts[1].strip() if len(parts) == 2 else line.strip()
            menu_map.setdefault(display_text, line)
    if not menu_map:
        return
    longest_entry = max(len(clear_option), max(len(txt) for txt in menu_map))
    menu_width = min(max_width, longest_entry)
    separator = "—" * (menu_width)
    options = [clear_option, separator] + list(menu_map.keys())
    fuzzel_cmd = [
        "fuzzel",
        "--dmenu",
        f"--config={config_path}",
        f"--lines={len(options)}",
        f"--width={menu_width}",
        "--x-margin=10",
    ]
    selection = run_cmd(fuzzel_cmd, check=False, input_text="\n".join(options))
    handle_selection(selection, separator, menu_map, clear_option)


if __name__ == "__main__":
    clipboard_fuzzel_menu()
