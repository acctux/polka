#!/usr/bin/env python3
import sys
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FolderItem:
    name: str
    icon: str
    location: str

    @property
    def label(self) -> str:
        return f"{self.icon} {self.name}"

    @property
    def path(self) -> Path:
        return Path(self.location).expanduser()


FOLDERS = [
    FolderItem("Documents", "󱧶", "~/Desktop/Documents"),
    FolderItem("Downloads", "󰉍", "~/Desktop/Downloads"),
    FolderItem("Videos", "", "~/Desktop/Videos"),
    FolderItem("Pictures", "󰉏", "~/Desktop/Pictures"),
    FolderItem("Projects", "󱧼", "~/Desktop/Projects"),
    FolderItem("Etc", "", "/etc"),
]


class VaultMenu:
    def __init__(self, plain_dir: Path, locked_dir: Path):
        self.plain_dir = plain_dir
        self.locked_dir = locked_dir
        self.is_mounted = (
            subprocess.run(["mountpoint", "-q", str(plain_dir)]).returncode == 0
        )

    def get_password(self, title: str):
        cmd = ["zenity", "--password", f"--title={title}"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.stdout.strip() if res.returncode == 0 else None

    def run_gocrypt(self, args: list[str], password: str):
        with tempfile.NamedTemporaryFile(mode="w", delete=True) as f:
            f.write(password)
            f.flush()
            subprocess.run(["gocryptfs"] + args + ["--passfile", f.name], check=True)

    def handle_vault(self):
        self.locked_dir.mkdir(parents=True, exist_ok=True)
        if not (self.locked_dir / "gocryptfs.conf").exists():
            if password := self.get_password("Enter init password"):
                self.run_gocrypt(["-init", str(self.locked_dir)], password)
            return
        if self.is_mounted:
            subprocess.run(["fusermount3", "-u", str(self.plain_dir)], check=True)
            try:
                self.plain_dir.rmdir()
            except OSError:
                pass
        else:
            self.plain_dir.mkdir(parents=True, exist_ok=True)
            cmd = ["gio", "set", str(self.plain_dir)]
            if UNLOCKED_ICON.exists():
                cmd += ["metadata::custom-icon", f"file://{UNLOCKED_ICON}"]
            subprocess.run(cmd, stderr=subprocess.DEVNULL)
            if password := self.get_password("Enter gocryptfs password"):
                self.run_gocrypt([str(self.locked_dir), str(self.plain_dir)], password)
                subprocess.Popen(["xdg-open", str(self.plain_dir), "&", "disown"])

    def run_menu(self, fuzzel_config: Path):
        vault_label = "󰉐 Lock Vault" if self.is_mounted else "󰉑 Unlock Vault"
        menu_options = {vault_label: "VAULT_ACTION", **{f.label: f for f in FOLDERS}}
        cmd = [
            "fuzzel",
            "--dmenu",
            f"--width={max(len(k) for k in menu_options.keys())}",
            f"--lines={len(menu_options)}",
        ]
        if fuzzel_config.exists():
            cmd += ["--config", str(fuzzel_config)]
        res = subprocess.run(
            cmd, input="\n".join(menu_options.keys()), text=True, capture_output=True
        )
        if res.returncode != 0:
            sys.exit(0)
        action = menu_options.get(res.stdout.strip())
        if action == "VAULT_ACTION":
            self.handle_vault()
        elif isinstance(action, FolderItem):
            subprocess.Popen(["xdg-open", str(action.path)])


if __name__ == "__main__":
    UNLOCKED_ICON: Path = Path(
        "/usr/share/icons/WhiteSur-dark/places/scalable/folder-unlocked.svg"
    )
    FUZZEL_CONFIG = Path.home() / ".config" / "fuzzel" / "waybar.ini"
    PLAIN_DIR = Path.home() / "Desktop/Decrypted"
    LOCKED_DIR = Path.home() / "Desktop/Private"
    VaultMenu(PLAIN_DIR, LOCKED_DIR).run_menu(FUZZEL_CONFIG)
