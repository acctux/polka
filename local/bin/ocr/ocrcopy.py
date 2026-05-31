#!/usr/bin/env python3
from pathlib import Path
import subprocess

CACHE_FILE = Path.home() / ".cache" / "ocr_region.png"


def main():
    try:
        region = subprocess.run(
            ["slurp"], capture_output=True, text=True
        ).stdout.strip()
        subprocess.run(["grim", "-g", region, str(CACHE_FILE)])
        cmd = ["tesseract", str(CACHE_FILE), "stdout", "-l", "eng"]
        text = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        ).stdout.strip()
        subprocess.run(["wl-copy"], input=text.encode())
        CACHE_FILE.unlink(missing_ok=True)
    except subprocess.CalledProcessError:
        subprocess.run(["notify-send", "OCR", "Tesseract failed"])
        return


if __name__ == "__main__":
    main()
