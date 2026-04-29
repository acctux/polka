#!/usr/bin/env python3
from pathlib import Path
import subprocess


def clipboard_fuzzel_menu(
    config_path=Path.home() / ".config" / "fuzzel" / "prompt.ini",
    max_width=64,
    max_lines=24,
    clear_options="Clear History",
) -> None:
    def run_cmd(cmd: list[str], input_text: str | None = None) -> str:
        return subprocess.run(
            cmd, input=input_text, text=True, capture_output=True
        ).stdout.strip()

    entries = [
        parts[1]
        for line in run_cmd(["cliphist", "list"]).splitlines()
        if (parts := line.strip().split(maxsplit=1)) and len(parts) == 2
    ]
    recent = entries[:max_lines]
    longest_entry_len = min(
        max_width,
        max((len(e) for e in recent + [clear_options]), default=0),
    )
    separator = "_" * longest_entry_len
    options = [clear_options, separator] + entries
    selection = run_cmd(
        [
            "fuzzel",
            "--dmenu",
            "--config",
            str(config_path),
            f"--lines={min(max_lines, len(options))}",
            f"--width={longest_entry_len + 2}",
            "--x-margin=10",
        ],
        "\n".join(options),
    )
    if selection == clear_options:
        run_cmd(["cliphist", "wipe"])
    elif selection and selection != separator:
        run_cmd(["wl-copy"], input_text=selection)


if __name__ == "__main__":
    clipboard_fuzzel_menu()
