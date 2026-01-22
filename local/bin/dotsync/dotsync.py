#!/usr/bin/env python3
import shutil
import subprocess
from pathlib import Path
from log import get_logger

log = get_logger("Polka")
HOME = Path.home()
CONFIG_DIR = HOME / ".config"
SHARE_DIR = HOME / ".local" / "share"
DOTFILES_DIR = HOME / "Polka"
DIRECTORIES_TO_LINK = [
    "config/systemd/user",
    "config/nvim",
    "local/bin",
]
BASE_DIR = HOME / "Lit/Docs/base"
INDIVIDUAL_DIRS = [
    (BASE_DIR / "fonts", SHARE_DIR / "fonts"),
    (BASE_DIR / "task", CONFIG_DIR / "task"),
    (BASE_DIR / "zsh", CONFIG_DIR / "zsh"),
]


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


def dotted_destination(src: Path, source_root: Path, target_root: Path) -> Path:
    parts = src.relative_to(source_root).parts
    return target_root / Path("." + parts[0], *parts[1:])


def deploy_dotfiles(dotfiles_dir, home_dir, dirs_to_link, individual_dirs):
    linked = 0
    if not dotfiles_dir.is_dir():
        log.error(f"Dotfiles directory does not exist: {dotfiles_dir}")
        return
    for src in dotfiles_dir.rglob("*"):
        if not src.is_file():
            continue
        if src.relative_to(dotfiles_dir).as_posix().startswith(".git") or any(
            src.relative_to(dotfiles_dir).is_relative_to(Path(d)) for d in dirs_to_link
        ):
            continue
        dst = dotted_destination(src, dotfiles_dir, home_dir)
        if link_path(src, dst):
            linked += 1
    for d in dirs_to_link:
        src = dotfiles_dir / d
        if not src.is_dir():
            log.error(f"{src} not found.")
            continue
        dst = dotted_destination(src, dotfiles_dir, home_dir)
        if link_path(src, dst):
            linked += 1
    for src_dir, dst_dir in individual_dirs:
        if not src_dir.is_dir():
            log.error(f"Directory does not exist: {src_dir}")
            continue
        for src_file in src_dir.rglob("*"):
            if not src_file.is_file():
                continue
            dst_file = dst_dir / src_file.relative_to(src_dir)
            if link_path(src_file, dst_file):
                linked += 1
    if shutil.which("hyprctl"):
        subprocess.run(["hyprctl", "reload"], check=False)
        log.info("Hyprland reloaded")
    log.info(f"Linked:{linked}")


if __name__ == "__main__":
    deploy_dotfiles(DOTFILES_DIR, HOME, DIRECTORIES_TO_LINK, INDIVIDUAL_DIRS)
