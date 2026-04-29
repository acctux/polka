#!/usr/bin/env python3
import sys
import os
import subprocess
from pathlib import Path

BASE_DIR = Path.home() / "Desktop" / "Games"


def create_prefix(base_dir: Path, game_name: str) -> Path:
    prefix_path = base_dir / game_name
    prefix_path.mkdir(parents=True, exist_ok=True)
    return prefix_path


def initialize_wine(prefix_path: Path) -> None:
    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix_path)
    try:
        subprocess.run(["wineboot", "--init"], env=env, check=True)
        print(f"Created Wine prefix at {prefix_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error initializing Wine prefix: {e}")
        sys.exit(1)


def get_game_name() -> str:
    try:
        result = subprocess.run(
            [
                "zenity",
                "--entry",
                "--title",
                "Game Name",
                "--text",
                "Enter directory name:",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()  # Remove any trailing newlines
    except subprocess.CalledProcessError as e:
        print(f"Error getting game name from zenity: {e}")
        sys.exit(1)


def main():
    game_name = get_game_name()
    if not game_name:
        print("No game name provided.")
        sys.exit(1)
    prefix_path = create_prefix(BASE_DIR, game_name)
    initialize_wine(prefix_path)


if __name__ == "__main__":
    main()
