#!/usr/bin/env python3

from dataclasses import dataclass
from typing import List
import sys
import os
import subprocess
from pathlib import Path
import logging


#########################
# LOG
#########################
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.INFO: "\033[36m",
        logging.WARNING: "\033[93m",
        logging.ERROR: "\033[31m",
    }
    RESET = "\033[0m"
    NAME = "\033[93m"

    def format(self, record):
        name = f"{self.NAME}{record.name}{self.RESET}"
        msg = f"{self.COLORS.get(record.levelno, '')}{record.getMessage()}{self.RESET}"
        return f"{name}: {msg}"


def get_logger(log_name=None, level=logging.INFO):
    log = logging.getLogger(log_name)
    if log.handlers:
        return log
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(ColorFormatter())
    log.addHandler(handler)
    log.setLevel(level)
    log.propagate = False
    return log


log = get_logger("Polka")


@dataclass
class PolkaConfig:
    dotfiles_dirs: List[str]
    skip_dirs: List[str] | None = None
    skip_files: List[str] | None = None


class PolkaDots:
    HOME = Path.home()

    def __init__(self, config: PolkaConfig):
        self.config = config
        self.dotfiles_paths = self._establish_dirs()
        self.skip_dirs = config.skip_dirs
        self.skip_files = config.skip_files

    def _establish_dirs(self) -> list[Path]:
        paths = []
        for d in config.dotfiles_dirs:
            dot_dir = self.HOME / d
            if dot_dir.is_dir():
                paths.append(self.HOME / d)
            else:
                log.warning(f"{dot_dir} not found, skipping.")
        return paths

    def _should_skip(self, parts: tuple[str, ...]) -> bool:
        if self.skip_files:
            if parts[-1] in self.skip_files:
                return True
        if self.skip_dirs:
            for part in parts:
                if part in self.skip_dirs:
                    return True
        return False

    def deploy(self):
        linked = 0
        for src_dir in self.dotfiles_paths:
            for src in src_dir.rglob("*"):
                if not src.is_file():
                    continue
                parts = src.relative_to(src_dir).parts
                if self._should_skip(parts):
                    continue
                dst = self.HOME / Path("." + parts[0], *parts[1:])
                rel = os.path.relpath(src, dst.parent)
                if dst.is_symlink() and os.readlink(dst) == rel:
                    continue
                if dst.exists() or dst.is_symlink():
                    dst.unlink()
                    log.info(f"Removed: {dst}")
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.symlink_to(rel)
                log.info(f"Linked: {dst} → {rel}")
                linked += 1
        log.info(f"Total linked: {linked}")
        if linked > 0:
            subprocess.run(["hyprctl", "reload"], check=False)
            log.info("Hyprland reloaded")


config = PolkaConfig(
    dotfiles_dirs=["Lit/polka", "Lit/Docs/secdots"],
    skip_dirs=[".git", "__pycache__", ".venv"],
    skip_files=[".gitignore"],
)
PolkaDots(config).deploy()
