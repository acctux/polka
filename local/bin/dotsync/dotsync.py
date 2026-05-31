#!/usr/bin/env python3

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
        logging.DEBUG: "\033[36m",  # cyan
        logging.INFO: "\033[34m",  # blue
        logging.WARNING: "\033[93m",  # yellow
        logging.ERROR: "\033[31m",  # red
    }
    RESET = "\033[0m"
    NAME_COLOR = "\033[93m"  # yellow

    def format(self, record):
        colored_name = f"{self.NAME_COLOR}{record.name}{self.RESET}"
        level_color = self.COLORS.get(record.levelno, "")
        colored_message = f"{level_color}{record.getMessage()}{self.RESET}"
        message = f"{colored_name}: {colored_message}"
        return message


def get_logger(log_name=None, level=logging.INFO):
    logger = logging.getLogger(log_name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(ColorFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


log = get_logger("Polka")


class PolkaDots:
    HOME = Path.home()
    SKIP_BASE = {".git", "__pycache__", ".venv"}
    SKIP_NAME = {".gitignore"}

    def __init__(self, dotfiles_dirs: list[str]):
        self.dotfiles_paths = [self.HOME / d for d in dotfiles_dirs]

    def deploy(self):
        linked = 0
        for src_dir in self.dotfiles_paths:
            if not src_dir.is_dir():
                log.warning(f"{src_dir} not found, skipping.")
                continue
            for src in src_dir.rglob("*"):
                if not src.is_file():
                    continue
                parts = src.relative_to(src_dir).parts
                for part in parts:
                    if part in self.SKIP_BASE:
                        continue
                if parts[-1] in self.SKIP_NAME:
                    continue
                dst = self.HOME / Path("." + parts[0], *parts[1:])
                dst.parent.mkdir(parents=True, exist_ok=True)
                rel = os.path.relpath(src, dst.parent)
                if dst.is_symlink() and os.readlink(dst) == rel:
                    continue
                if dst.exists() or dst.is_symlink():
                    dst.unlink()
                    log.info(f"Removed: {dst}")
                dst.symlink_to(rel)
                log.info(f"Linked: {dst} → {rel}")
                linked += 1
        log.info(f"Total linked: {linked}")
        subprocess.run(["hyprctl", "reload"], check=False)
        log.info("Hyprland reloaded")


PolkaDots(["Lit/polka", "Lit/Docs/secdots"]).deploy()
