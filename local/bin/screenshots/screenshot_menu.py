#!/usr/bin/env python3
import subprocess
from datetime import datetime
from pathlib import Path

# -----------------------------
# Config
# -----------------------------
SCREENSHOTS_DIR = Path.home() / "Desktop" / "Pictures" / "Screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG = Path.home() / ".config/fuzzel/fav-menu.ini"
CACHE_FILE = Path.home() / ".cache" / "ocr_copy" / "ocr_region.png"


# -----------------------------
# Helpers
# -----------------------------
def timestamped_file():
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return SCREENSHOTS_DIR / f"screenshot_{ts}.png"


def run(cmd):
    subprocess.run(cmd, check=False)


def copy_to_clipboard(file):
    if file.exists():
        with file.open("rb") as f:
            subprocess.run(["wl-copy"], input=f.read(), check=False)


def get_region():
    """Safely get region from slurp. Returns None if cancelled."""
    try:
        region = subprocess.check_output(["slurp"]).decode().strip()
        return region if region else None
    except subprocess.CalledProcessError:
        return None


# -----------------------------
# Screenshot actions
# -----------------------------
def full_copy():
    file = timestamped_file()
    run(["grim", str(file)])
    copy_to_clipboard(file)


def full_edit():
    file = timestamped_file()
    run(["grim", str(file)])
    run(["swappy", "-f", str(file)])


def region_copy():
    region = get_region()
    if not region:
        return
    file = timestamped_file()
    run(["grim", "-g", region, str(file)])
    copy_to_clipboard(file)


def region_edit():
    region = get_region()
    if not region:
        return
    file = timestamped_file()
    run(["grim", "-g", region, str(file)])
    run(["swappy", "-f", str(file)])


# -----------------------------
# OCR / Text Actions
# -----------------------------
def region_text():
    """Integrated OCR logic from previous ocrcopy.py"""
    region = get_region()
    if not region:
        return

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    grim_proc = subprocess.run(["grim", "-g", region, str(CACHE_FILE)], check=False)
    if grim_proc.returncode != 0:
        return

    try:
        cmd = ["tesseract", str(CACHE_FILE), "stdout", "-l", "eng"]
        text = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        ).stdout.strip()
        if text:
            subprocess.run(["wl-copy"], input=text, text=True, check=False)
    except subprocess.CalledProcessError:
        subprocess.run(["notify-send", "OCR", "Tesseract failed"], check=False)
    finally:
        CACHE_FILE.unlink(missing_ok=True)


# -----------------------------
# Menu actions
# -----------------------------
def open_folder():
    run(["xdg-open", str(SCREENSHOTS_DIR)])


def run_script(path, args=None):
    cmd = [str(path)]
    if args:
        cmd.extend(args)
    run(cmd)


# -----------------------------
# Menu Definition
# -----------------------------
MENU = [
    "Full Screen → Copy",
    "Full Screen → Edit",
    "Region → Copy",
    "Region → Edit",
    "",
    "Region → Text",
    "OCR Region",
    "OCR Capture",
    "OCR → PDF",
    "",
    "Open Screenshots",
    "Cancel",
]

ACTIONS = {
    "Full Screen → Copy": full_copy,
    "Full Screen → Edit": full_edit,
    "Region → Copy": region_copy,
    "Region → Edit": region_edit,
    "Region → Text": region_text,  # Now points to internal function
    "OCR Region": lambda: run_script(
        Path.home() / ".local/bin/screenshots/maim_pdf.py", ["region"]
    ),
    "OCR Capture": lambda: run_script(
        Path.home() / ".local/bin/screenshots/maim_pdf.py", ["capture"]
    ),
    "OCR → PDF": lambda: run_script(
        Path.home() / ".local/bin/screenshots/maim_pdf.py", ["ocr"]
    ),
    "Open Screenshots": open_folder,
    "Cancel": lambda: None,
}


# -----------------------------
# Execution
# -----------------------------
def main():
    menu_str = "\n".join(MENU)
    result = subprocess.run(
        [
            "fuzzel",
            "--dmenu",
            "--hide-prompt",
            f"--lines={len(MENU)}",
            f"--width={max(len(x) for x in MENU)}",
            f"--config={CONFIG}",
        ],
        input=menu_str.encode(),
        stdout=subprocess.PIPE,
    )
    choice = result.stdout.decode().strip()
    action = ACTIONS.get(choice)
    if action:
        action()


if __name__ == "__main__":
    main()
