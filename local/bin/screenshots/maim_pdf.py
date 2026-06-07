#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


class MaimPdfTool:
    def __init__(self):
        HOME = Path.home()
        self.base = HOME / ".cache" / "ocr"
        self.screens = self.base / "screens"
        self.noalpha = self.base / "noalpha"
        self.region_file = self.base / "region.txt"
        self.output_pdf = HOME / "Desktop" / "Documents" / "ocr_output.pdf"

    def _run(self, *cmd):
        subprocess.run(cmd, check=True)

    def _notify(self, msg):
        self._run("notify-send", msg)

    def _mkdirs(self, *paths):
        for p in paths:
            p.mkdir(parents=True, exist_ok=True)

    # ---------- region ----------
    def select_region(self):
        region = subprocess.check_output(["slurp"], text=True).strip()
        self.region_file.parent.mkdir(parents=True, exist_ok=True)
        self.region_file.write_text(region)
        self._notify(f"Saved: {region}")

    # ---------- capture ----------
    def _load_region(self):
        if not self.region_file.exists():
            raise RuntimeError("Run select-region first")
        region = self.region_file.read_text().strip()
        if not region:
            raise RuntimeError("Empty region file")
        return region

    def _next_index(self) -> int:
        self._mkdirs(self.screens)
        pngs = sorted(self.screens.glob("*.png"))
        if not pngs:
            return 0
        return int(pngs[-1].stem) + 1

    def capture(self) -> None:
        self._mkdirs(self.screens)
        region = self._load_region()
        screen_path = self.screens / f"{self._next_index():03d}.png"
        self._run("grim", "-g", region, str(screen_path))
        self._notify(f"Saved screenshot: {screen_path.name}")

    # ---------- OCR ----------
    def ocr_2_pdf(self):
        self._mkdirs(self.noalpha)
        self._run(
            "mogrify",
            "-path",
            str(self.noalpha),
            "-alpha",
            "remove",
            "-alpha",
            "off",
            str(self.screens / "*.png"),
        )
        noalpha_images = sorted(self.noalpha.glob("*.png"))
        if not noalpha_images:
            raise RuntimeError("No images found")
        tmp_pdf = self.base / "tmp.pdf"
        self._run(
            "img2pdf",
            *map(str, noalpha_images),
            "-o",
            str(tmp_pdf),
        )
        self._run(
            "ocrmypdf",
            "--language",
            "eng",
            "--output-type",
            "pdf",
            "--jpeg-quality",
            "100",
            str(tmp_pdf),
            str(self.output_pdf),
        )
        tmp_pdf.unlink(missing_ok=True)
        for no_alpha_screenshot in self.noalpha.glob("*"):
            no_alpha_screenshot.unlink()
        self.noalpha.rmdir()
        self._notify(f"OCR saved: {self.output_pdf}")


def main():
    parser = argparse.ArgumentParser(prog="maim_pdf")
    parser.add_argument(
        "cmd",
        choices=[
            "region",
            "capture",
            "ocr",
        ],
        help="Command to run",
    )
    args = parser.parse_args()
    tool = MaimPdfTool()
    if args.cmd == "region":
        tool.select_region()
    elif args.cmd == "capture":
        tool.capture()
    elif args.cmd == "ocr":
        tool.ocr_2_pdf()


if __name__ == "__main__":
    main()
