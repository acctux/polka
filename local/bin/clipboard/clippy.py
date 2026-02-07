#!/usr/bin/env python3

from pathlib import Path
import subprocess

config_path = Path.home() / ".config" / "fuzzel" / "clipboard.ini"


def run_fuzzel(options: list[str], config: Path) -> str:
    result = subprocess.run(
        [
            "fuzzel",
            "--dmenu",
            "--config",
            str(config),
        ],
        input="\n".join(options),
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def get_cleaned_clipboard_history() -> list[str]:
    cliphist_output = subprocess.check_output(["cliphist", "list"], text=True)
    cleaned_history = [
        line.split(maxsplit=1)[1]
        for line in cliphist_output.splitlines()
        if line.strip()
    ]
    return cleaned_history


def main():
    cleaned_history = get_cleaned_clipboard_history()
    options = [
        "Clear History",
        "______________________________________",
    ] + cleaned_history
    selected_item = run_fuzzel(options, config_path)
    if selected_item == "Clear History":
        subprocess.run(["cliphist", "wipe"])
    elif selected_item:
        subprocess.run(["wl-copy"], input=selected_item, text=True)


if __name__ == "__main__":
    main()

