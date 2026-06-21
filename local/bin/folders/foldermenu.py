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


FUZZEL_CONFIG = Path.home() / ".config" / "fuzzel" / "waybar.ini"
FOLDERS = [
    FolderItem("Documents", "󱧶", "~/Desktop/Documents"),
    FolderItem("Downloads", "󰉍", "~/Desktop/Downloads"),
    FolderItem("Videos", "", "~/Desktop/Videos"),
    FolderItem("Pictures", "󰉏", "~/Desktop/Pictures"),
    FolderItem("Projects", "󱧼", "~/Desktop/Projects"),
    FolderItem("Etc", "", "/etc"),
]
PLAIN_DIR = Path.home() / "Desktop/Decrypted"
LOCKED_DIR = Path.home() / "Desktop/Private"
UNLOCKED_ICON: Path = Path(
    "/usr/share/icons/WhiteSur-dark/places/scalable/folder-unlocked.svg"
)


class FolderMenu:
    def __init__(
        self, plain_dir: Path, locked_dir: Path, fuzzel_config: Path, unlock_icon: Path
    ):
        self.plain_dir = plain_dir
        self.locked_dir = locked_dir
        self.fuzzel_config = fuzzel_config
        self.unlock_icon = unlock_icon
        self.is_mounted = self._is_mnt()

    def _is_mnt(self) -> bool:
        return subprocess.run(["mountpoint", "-q", str(self.plain_dir)]).returncode == 0

    def get_password(self, title: str) -> str:
        cmd = ["zenity", "--password", f"--title={title}"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.stdout.strip() if res.returncode == 0 else ""

    def run_gocrypt(self, args: list[str], password: str) -> None:
        with tempfile.NamedTemporaryFile(mode="w", delete=True) as f:
            f.write(password)
            f.flush()
            subprocess.run(["gocryptfs"] + args + ["--passfile", f.name], check=True)

    def handle_vault(self, icon: Path) -> None:
        self.locked_dir.mkdir(parents=True, exist_ok=True)
        if not (self.locked_dir / "gocryptfs.conf").exists():
            if password := self.get_password("Enter init password"):
                self.run_gocrypt(["-init", str(self.locked_dir)], password)
            return
        if self.is_mounted:
            try:
                cmd = ["fusermount3", "-u", str(self.plain_dir)]
                subprocess.run(cmd, check=True)
                self.plain_dir.rmdir()
            except Exception:
                pass
        else:
            self.plain_dir.mkdir(parents=True, exist_ok=True)
            cmd = ["gio", "set", str(self.plain_dir)]
            if icon.exists():
                cmd += ["metadata::custom-icon", f"file://{icon}"]
            subprocess.run(cmd, stderr=subprocess.DEVNULL)
            if password := self.get_password("Enter gocryptfs password"):
                self.run_gocrypt([str(self.locked_dir), str(self.plain_dir)], password)
                subprocess.Popen(["xdg-open", str(self.plain_dir), "&", "disown"])

    def run(self) -> None:
        vault_label = "󰉑 Unlock Vault"
        if self.is_mounted:
            vault_label = "󰉐 Lock Vault"
        menu_options = {vault_label: "VAULT_ACTION", **{f.label: f for f in FOLDERS}}
        width = max(len(k) for k in menu_options.keys())
        lines = len(menu_options)
        cmd = [
            "fuzzel",
            "--dmenu",
            f"--width={width}",
            f"--lines={lines}",
            "--config",
            str(self.fuzzel_config),
        ]
        input = "\n".join(menu_options.keys())
        res = subprocess.run(cmd, input=input, text=True, capture_output=True)
        if res.returncode != 0:
            sys.exit(0)
        action = menu_options.get(res.stdout.strip())
        if action == "VAULT_ACTION":
            self.handle_vault(self.unlock_icon)
        elif isinstance(action, FolderItem):
            subprocess.Popen(["xdg-open", str(action.path)])


if __name__ == "__main__":
    FolderMenu(PLAIN_DIR, LOCKED_DIR, FUZZEL_CONFIG, UNLOCKED_ICON).run()
