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
dirs_to_link: list[str] = ["local/bin"]


##########################################
# HELPERS
##########################################
def link_path(src: Path, dst: Path) -> bool:
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


def dotted_destination(src: Path, source_dir: Path, target_dir: Path) -> Path:
    parts = src.relative_to(source_dir).parts
    return target_dir / Path("." + parts[0], *parts[1:])


def collect_candidates(
    base_dir: Path, home: Path, dirs_to_skip: list[str]
) -> list[tuple[Path, Path]]:
    """Return list of (src, dst) tuples for all files in base_dir, skipping certain dirs."""
    candidates = []
    for src in base_dir.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(base_dir)
        if rel.parts[0] == ".git":
            continue
        if any(rel.parts[0] == d.split("/")[0] for d in dirs_to_skip):
            continue
        candidates.append((src, dotted_destination(src, base_dir, home)))
    return candidates


def file_candidates() -> list[tuple[Path, Path]]:
    """Return list of (src, dst) tuples to link."""
    candidates = []
    candidates.extend(collect_candidates(dotfiles_dir, home, dirs_to_link))
    candidates.extend(collect_candidates(secdots_dir, home, dirs_to_link))
    for d in dirs_to_link:
        src = dotfiles_dir / d
        if src.is_dir():
            candidates.append((src, dotted_destination(src, dotfiles_dir, home)))
    return candidates


##########################################
# MAIN
##########################################
def deploy_dotfiles():
    if not dotfiles_dir.is_dir():
        log.error(f"Dotfiles directory not found: {dotfiles_dir}")
        return
    linked = 0
    for src, dst in file_candidates():
        if link_path(src, dst):
            linked += 1
    if shutil.which("hyprctl"):
        subprocess.run(["hyprctl", "reload"], check=False)
        log.info("Hyprland reloaded")
    log.info(f"Total linked:\033[0m {linked}")


##########################################
# ENTRY
##########################################
if __name__ == "__main__":
    deploy_dotfiles()

