#!/usr/bin/env python3
from pathlib import Path
import subprocess


CONFIG_PATH = Path.home() / ".config" / "fuzzel" / "clipboard.ini"
MAX_WIDTH = 44
MAX_LINES = 30


def clipboard_fuzzel_menu(
    config_path=CONFIG_PATH, max_width=MAX_WIDTH, max_lines=MAX_LINES
) -> None:
    def run_cmd(cmd: list[str], input_text: str | None = None) -> str:
        out = subprocess.run(cmd, input=input_text, text=True, capture_output=True)
        return out.stdout.strip()

    entries = []
    output = run_cmd(["cliphist", "list"])
    for line in output.splitlines():
        line = line.strip()
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        entry = parts[1]
        entries.append(entry)
    recent = entries[:max_lines]
    clear_option = "Clear History"
    lengths = []
    for option in recent + [clear_option]:
        lengths.append(len(option))
    longest_entry_len = min(max_width, max(lengths))
    separator = "_" * longest_entry_len
    options = [clear_option, separator] + entries
    cmd = [
        "fuzzel",
        "--dmenu",
        "--config",
        str(config_path),
        f"--lines={min(max_lines, len(options))}",
        f"--width={longest_entry_len + 2}",
        "--x-margin=10",
    ]
    selection = run_cmd(cmd, "\n".join(options))
    if selection == clear_option:
        cmd = ["cliphist", "wipe"]
        run_cmd(cmd)
    elif selection and selection != separator:
        cmd = ["wl-copy"]
        run_cmd(cmd, input_text=selection)


if __name__ == "__main__":
    clipboard_fuzzel_menu()
