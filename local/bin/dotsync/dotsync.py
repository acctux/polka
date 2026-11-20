#!/usr/bin/env python3

import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

DOT_DIRS = ["Lit/polka", "Lit/Docs/secdots"]
SKIP_DIRS = [".git", "__pycache__", ".venv"]
SKIP_FILES = [".gitignore"]


class ColorFormatter(logging.Formatter):
    RESET = "\033[0m"
    NAME = "\033[93m"

    def __init__(self):
        self.COLORS = {
            logging.INFO: "\033[36m",
            logging.WARNING: "\033[93m",
            logging.ERROR: "\033[31m",
        }

    def format(self, record: logging.LogRecord) -> str:
        name = f"{self.NAME}{record.name}{self.RESET}"
        color = self.COLORS.get(record.levelno, "")
        message = f"{color}{record.getMessage()}{self.RESET}"
        return f"{name}: {message}"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(ColorFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(level)
    return logger


log = get_logger("Polka")


@dataclass
class PolkaConfig:
    dotfiles_dirs: list[str]
    skip_dirs: list[str]
    skip_files: list[str]


class PolkaDots:
    def __init__(self, config: PolkaConfig):
        self.config = config
        self.home = Path.home()
        self.dotfiles_paths = self._establish_dirs()

    def _establish_dirs(self) -> list[Path]:
        paths = []
        for directory in self.config.dotfiles_dirs:
            path = self.home / directory
            if path.is_dir():
                paths.append(path)
            else:
                log.warning("%s not found, skipping.", path)
        return paths

    def _should_skip(self, relative_path: Path) -> bool:
        return relative_path.name in self.config.skip_files or any(
            part in self.config.skip_dirs for part in relative_path.parts
        )

    def _destination_for(self, relative_path: Path) -> Path:
        parts = relative_path.parts
        return self.home / Path(f".{parts[0]}", *parts[1:])

    def _link_file(self, source: Path, destination: Path) -> bool:
        destination.parent.mkdir(parents=True, exist_ok=True)
        target = os.path.relpath(source, destination.parent)

        if destination.is_symlink() and os.readlink(destination) == target:
            return False

        if destination.exists() or destination.is_symlink():
            destination.unlink()
            log.info("Removed: %s", destination)

        destination.symlink_to(target)
        log.info("Linked: %s → %s", destination, target)
        return True

    def deploy(self) -> None:
        linked = 0

        for source_dir in self.dotfiles_paths:
            for source in source_dir.rglob("*"):
                if not source.is_file():
                    continue

                relative_path = source.relative_to(source_dir)
                if self._should_skip(relative_path):
                    continue

                destination = self._destination_for(relative_path)
                linked += self._link_file(source, destination)

        log.info("Total linked: %d", linked)

        if linked:
            subprocess.run(["hyprctl", "reload"], check=False)
            log.info("Hyprland reloaded")


if __name__ == "__main__":
    config = PolkaConfig(DOT_DIRS, SKIP_DIRS, SKIP_FILES)
    PolkaDots(config).deploy()
