#!/usr/bin/env python3
import shutil
import subprocess
from pathlib import Path
import logging
import sys
import os


#########################
# LOG
#########################
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",  # cyan
        logging.INFO: "\033[34m",  # blue
        logging.WARNING: "\033[93m",  # yellow
        logging.ERROR: "\033[31m",  # red
        logging.CRITICAL: "\033[41m",  # red background
    }
    RESET = "\033[0m"
    UNDERLINE = "\033[4m"
    NAME_COLOR = "\033[93m"  # yellow

    def format(self, record):
        colored_name = f"{self.NAME_COLOR}{record.name}{self.RESET}"
        level_color = self.COLORS.get(record.levelno, "")
        colored_message = f"{level_color}{record.getMessage()}{self.RESET}"
        message = f"{colored_name}: {colored_message}"
        if record.levelno == logging.CRITICAL:
            message = f"{self.UNDERLINE}{message}{self.RESET}"
        return message


def get_logger(log_name: str | None = None, level=logging.INFO):
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


##########################################
# DATA CLASSES
##########################################
home: Path = Path.home()
dotfiles_dir: Path = home / "Lit" / "polka"
secdots_dir: Path = home / "Lit" / "Docs" / "secdots"


class PolkaConfiguration:
    def __init__(
        self,
        home: Path,
        dotfiles_dir: Path,
        secdots_dir: Path,
    ):
        self.home = home
        self.dotfile_path = dotfiles_dir
        self.secdot_path = secdots_dir

    def link_path(self, src: Path, dst: Path) -> bool:
        """Create a symlink, replacing existing files/folders if necessary."""
        dst.parent.mkdir(parents=True, exist_ok=True)
        rel = os.path.relpath(src, dst.parent)
        if dst.is_symlink() and os.readlink(dst) == rel:
            return False
        if dst.exists() or dst.is_symlink():
            if dst.is_dir() and not dst.is_symlink():
                shutil.rmtree(dst)
            else:
                dst.unlink()
            log.info(f"Removed: {dst}")
        dst.symlink_to(rel, target_is_directory=src.is_dir())
        log.info(f"Linked: {dst} → {rel}")
        return True

    def dotted_destination(self, src: Path, source_dir: Path) -> Path:
        """Return the destination path with a dot-prefixed top-level folder."""
        parts = src.relative_to(source_dir).parts
        return self.home / Path("." + parts[0], *parts[1:])

    def collect_candidates(self, base_dir: Path) -> list[tuple[Path, Path]]:
        """Collect all files in base_dir, skipping unwanted dirs."""
        candidates = []
        for src in base_dir.rglob("*"):
            if not src.is_file():
                continue
            rel = src.relative_to(base_dir)
            if rel.parts[0] == ".git":
                continue
            candidates.append((src, self.dotted_destination(src, base_dir)))
        return candidates

    def file_candidates(self) -> list[tuple[Path, Path]]:
        """Get all candidate files and directories for linking from dotfiles and secdots."""
        candidates: list[tuple[Path, Path]] = []
        candidates.extend(self.collect_candidates(self.dotfile_path))
        candidates.extend(self.collect_candidates(self.secdot_path))
        return candidates

    def deploy(self):
        """Automate the linking of all dotfiles."""
        if not self.dotfile_path.is_dir():
            log.error(f"Dotfiles directory not found: {self.dotfile_path}")
            return
        linked = 0
        for src, dst in self.file_candidates():
            if self.link_path(src, dst):
                linked += 1
        if shutil.which("hyprctl"):
            subprocess.run(["hyprctl", "reload"], check=False)
            log.info("Hyprland reloaded")
        log.info(f"Total linked: {linked}")


##########################################
# ENTRY
##########################################
if __name__ == "__main__":
    polka = PolkaConfiguration(home, dotfiles_dir, secdots_dir)
    polka.deploy()
