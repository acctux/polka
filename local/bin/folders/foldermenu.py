#!/usr/bin/env python3
import sys
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

LOCKED_DIR = Path.home() / "Desktop/Private"
PLAIN_DIR = Path.home() / "Desktop/Decrypted"
FUZZEL_CONFIG = Path.home() / ".config/fuzzel/waybar.ini"
PLAIN_ICON = "file:///usr/share/icons/WhiteSur-dark/places/scalable/folder-unlocked.svg"


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
    FolderItem("Music", "󱧶", "~/Desktop/Music"),
    FolderItem("Downloads", "󰉍", "~/Desktop/Downloads"),
    FolderItem("Videos", "", "~/Desktop/Videos"),
    FolderItem("Pictures", "󰉏", "~/Desktop/Pictures"),
    FolderItem("Projects", "󱧼", "~/Desktop/Projects"),
    FolderItem("Configs", "", "~/.config"),
]


class VaultMenu:
    def __init__(self):
        cmd = ["mountpoint", "-q", str(PLAIN_DIR)]
        self.is_mounted = subprocess.run(cmd).returncode == 0

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
        LOCKED_DIR.mkdir(parents=True, exist_ok=True)
        if not (LOCKED_DIR / "gocryptfs.conf").exists():
            if password := self.get_password("Enter init password"):
                self.run_gocrypt(["-init", str(LOCKED_DIR)], password)
            return
        if self.is_mounted:
            subprocess.run(["fusermount3", "-u", str(PLAIN_DIR)], check=True)
            try:
                PLAIN_DIR.rmdir()
            except OSError:
                pass
        else:
            PLAIN_DIR.mkdir(parents=True, exist_ok=True)
            cmd = ["gio", "set", str(PLAIN_DIR), "metadata::custom-icon", PLAIN_ICON]
            subprocess.run(cmd, stderr=subprocess.DEVNULL)
            if password := self.get_password("Enter gocryptfs password"):
                self.run_gocrypt([str(LOCKED_DIR), str(PLAIN_DIR)], password)
                subprocess.Popen(["xdg-open", str(PLAIN_DIR)])

    def run_menu(self):
        vault_label = "󰉐 Lock Vault" if self.is_mounted else "󰉑 Unlock Vault"
        menu_options = {vault_label: "VAULT_ACTION", **{f.label: f for f in FOLDERS}}
        cmd = [
            "fuzzel",
            "--dmenu",
            f"--width={max(len(k) for k in menu_options.keys()) + 2}",
            f"--lines={len(menu_options)}",
            "--x-margin=15",
        ]
        if FUZZEL_CONFIG.exists():
            cmd += ["--config", str(FUZZEL_CONFIG)]
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
    VaultMenu().run_menu()
