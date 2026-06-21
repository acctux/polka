#!/usr/bin/env python3

import sys
import os
import subprocess
from pathlib import Path

BASE_DIR = Path.home() / "Desktop" / "Games"


def get_game_prefix_path(base_dir: Path) -> Path:
    try:
        game_prefixes = []
        for d in base_dir.iterdir():
            if d.is_dir():
                game_prefixes.append(d.name)
        cmd = [
            "zenity",
            "--list",
            "--title",
            "Select Game Prefix",
            "--column",
            "Game Prefix",
        ] + game_prefixes
        selected_prefix = subprocess.check_output(cmd, universal_newlines=True).strip()
        if not selected_prefix:
            print("No game prefix selected.")
            sys.exit(1)
        return base_dir / selected_prefix
    except subprocess.CalledProcessError:
        print("Error selecting game prefix.")
        sys.exit(1)


def select_game() -> str:
    try:
        cmd = ["zenity", "--file-selection", "--title", "Select Game Executable"]
        return subprocess.check_output(cmd, universal_newlines=True).strip()
    except subprocess.CalledProcessError:
        print("No file selected or an error occurred.")
        sys.exit(1)


def run_with_wine(file_path: str, prefix_path: Path) -> None:
    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix_path)
    try:
        cmd = ["wine", file_path]
        subprocess.run(cmd, env=env, check=True)
        print(f"Running: {file_path} in prefix {prefix_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running {file_path}: {e}")
        sys.exit(1)


def main():
    prefix_path = get_game_prefix_path(BASE_DIR)
    selected_file = select_game()
    if not Path(selected_file).exists():
        print(f"{selected_file}: does not exist")
        sys.exit(1)
    run_with_wine(selected_file, prefix_path)


if __name__ == "__main__":
    main()
