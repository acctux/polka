#!/usr/bin/env python3
import shutil
import subprocess
from pathlib import Path
import logging
import sys

##########################################
# CONFIG
##########################################
HOME = Path.home()
CONFIG_DIR = HOME / ".config"
SHARE_DIR = HOME / ".local" / "share"
DOTS_P = HOME / "Lit" / "polka"
BASE = HOME / "Lit/Docs/base"
##########################################
dirs_to_link = ["config/systemd/user", "local/bin"]
ind_dirs = [
    ((BASE / "fonts"), (SHARE_DIR / "fonts")),
    ((BASE / "task"), (CONFIG_DIR / "task")),
    ((BASE / "zsh"), (CONFIG_DIR / "zsh")),
    ((BASE / "git"), (CONFIG_DIR / "git")),
    ((BASE / "gh"), (CONFIG_DIR / "git")),
]


##########################################
# LOG
##########################################
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.INFO: "\033[34m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[31m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = ColorFormatter("%(name)s %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = get_logger("Polka")


############################
# Helpers
############################
def link_path(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    rel = src.relative_to(dst.parent, walk_up=True)
    if dst.is_symlink() and dst.readlink() == rel:
        return False
    if dst.exists():
        if dst.is_dir() and not dst.is_symlink():
            shutil.rmtree(dst)
        else:
            dst.unlink(missing_ok=True)
        log.info(f"Removed: {dst}")
    dst.symlink_to(rel, target_is_directory=src.is_dir())
    log.info(f"Linked: {dst} → {rel}")
    return True


def dotted_destination(src: Path, source_dir: Path, target_dir: Path) -> Path:
    parts = src.relative_to(source_dir).parts
    return target_dir / Path("." + parts[0], *parts[1:])


def file_candidates(
    target_dir: Path,
    dotfiles_dir: Path,
    dirs_to_link: list[str],
    ind_dirs: list[tuple[Path, Path]],
):
    for src in dotfiles_dir.rglob("*"):
        if src.is_file():
            rel = src.relative_to(dotfiles_dir)
            if rel.parts[0] == ".git":
                continue
            if any(rel.is_relative_to(Path(d)) for d in dirs_to_link):
                continue
            yield src, dotted_destination(src, dotfiles_dir, target_dir)
    for d in dirs_to_link:
        src = dotfiles_dir / d
        if src.is_dir():
            yield src, dotted_destination(src, dotfiles_dir, target_dir)
    for src_dir, dst_dir in ind_dirs:
        if not src_dir.is_dir():
            continue
        for src in src_dir.rglob("*"):
            if src.is_file():
                yield src, dst_dir / src.relative_to(src_dir)


############################
# Main
############################
def deploy_dotfiles(
    HOME: Path,
    dot_dir: Path,
    dirs_to_link: list[str],
    ind_dirs: list[tuple[Path, Path]],
):
    if not dot_dir.is_dir():
        log.error(f"Dotfiles directory not found: {dot_dir}")
        return
    linked = 0
    for src, dst in file_candidates(HOME, dot_dir, dirs_to_link, ind_dirs):
        if link_path(src, dst):
            linked += 1
    if shutil.which("hyprctl"):
        subprocess.run(["hyprctl", "reload"], check=False)
        log.info("Hyprland reloaded")
    log.info(f"Linked: {linked}")


if __name__ == "__main__":
    deploy_dotfiles(HOME, DOTS_P, dirs_to_link, ind_dirs)
