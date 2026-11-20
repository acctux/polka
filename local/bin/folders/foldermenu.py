#!/usr/bin/env python3

import subprocess
import tempfile
from pathlib import Path

HOME = Path.home()
DESKTOP = HOME / "Desktop"
PLAIN_DIR = DESKTOP / "Decrypted"
LOCKED_DIR = DESKTOP / "Private"
FUZZEL_CONFIG = HOME / ".config/fuzzel/waybar.ini"
UNLOCKED_ICON = Path(
    "/usr/share/icons/WhiteSur-dark/places/scalable/folder-unlocked.svg"
)
FOLDERS = {
    "󱧶 Documents": DESKTOP / "Documents",
    "󰉍 Downloads": DESKTOP / "Downloads",
    " Videos": DESKTOP / "Videos",
    "󰉏 Pictures": DESKTOP / "Pictures",
    "󱧼 Projects": DESKTOP / "Projects",
    " Etc": "/etc",
}
VAULT_LABELS = {
    False: "󰉑 Unlock Vault",
    True: "󰉐 Lock Vault",
}


def manage_vault(mounted: bool) -> None:
    if mounted:
        subprocess.run(["fusermount3", "-u", str(PLAIN_DIR)], check=True)
        PLAIN_DIR.rmdir()
    else:
        result = subprocess.run(
            ["zenity", "--password", "--title=Enter gocryptfs password"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return
        cryptpass = result.stdout.strip()
        PLAIN_DIR.mkdir(parents=True, exist_ok=True)
        if UNLOCKED_ICON.exists():
            subprocess.run(
                [
                    "gio",
                    "set",
                    str(PLAIN_DIR),
                    "metadata::custom-icon",
                    UNLOCKED_ICON.as_uri(),
                ],
                check=False,
                stderr=subprocess.DEVNULL,
            )
        with tempfile.NamedTemporaryFile(mode="w") as password_file:
            password_file.write(cryptpass)
            password_file.flush()
            subprocess.run(
                [
                    "gocryptfs",
                    str(LOCKED_DIR),
                    str(PLAIN_DIR),
                    "--passfile",
                    password_file.name,
                ],
                check=True,
            )
        subprocess.Popen(["xdg-open", str(PLAIN_DIR)])


def choose_folder(mounted: bool) -> str:
    options = [VAULT_LABELS[mounted], *FOLDERS]
    result = subprocess.run(
        [
            "fuzzel",
            "--dmenu",
            f"--width={max(map(len, options))}",
            f"--lines={len(options)}",
            "--config",
            str(FUZZEL_CONFIG),
        ],
        input="\n".join(options),
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        return ""

    return result.stdout.strip()


def show_menu() -> None:
    mounted = (
        subprocess.run(
            ["mountpoint", "-q", str(PLAIN_DIR)],
            check=False,
        ).returncode
        == 0
    )

    selection = choose_folder(mounted)
    if not selection:
        return

    if selection in VAULT_LABELS.values():
        manage_vault(mounted)
    elif selection in FOLDERS:
        subprocess.Popen(["xdg-open", str(FOLDERS[selection])])


if __name__ == "__main__":
    show_menu()
