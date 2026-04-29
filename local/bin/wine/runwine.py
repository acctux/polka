#!/usr/bin/env python3

import sys
import os
import subprocess
from pathlib import Path

BASE_DIR = Path.home() / "Desktop" / "Games"


def get_game_prefix_path() -> Path:
    try:
        game_prefixes = [str(d.name) for d in BASE_DIR.iterdir() if d.is_dir()]
        selected_prefix = subprocess.check_output(
            [
                "zenity",
                "--list",
                "--title",
                "Select Game Prefix",
                "--column",
                "Game Prefix",
            ]
            + game_prefixes,
            universal_newlines=True,
        ).strip()
        if not selected_prefix:
            print("No game prefix selected.")
            sys.exit(1)
        return BASE_DIR / selected_prefix
    except subprocess.CalledProcessError:
        print("Error selecting game prefix.")
        sys.exit(1)


def select_file() -> str:
    try:
        selected_file = subprocess.check_output(
            ["zenity", "--file-selection", "--title", "Select Game Executable"],
            universal_newlines=True,
        ).strip()
        return selected_file
    except subprocess.CalledProcessError:
        print("No file selected or an error occurred.")
        sys.exit(1)


def validate_file(file_path: str) -> None:
    if not Path(file_path).exists():
        print(f"Selected file does not exist: {file_path}")
        sys.exit(1)


def run_with_wine(file_path: str, prefix_path: Path) -> None:
    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix_path)
    try:
        subprocess.run(["wine", file_path], env=env, check=True)
        print(f"Running {file_path} with Wine from prefix {prefix_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running {file_path}: {e}")
        sys.exit(1)


def main():
    prefix_path = get_game_prefix_path()
    selected_file = select_file()
    validate_file(selected_file)
    run_with_wine(selected_file, prefix_path)


if __name__ == "__main__":
    main()
