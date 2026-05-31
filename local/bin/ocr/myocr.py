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

    def _ensure(self, *paths):
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
        self._ensure(self.screens)
        max_index = -1
        for path in self.screens.glob("*.png"):
            if path.stem.isdigit():
                num = int(path.stem)
                if num > max_index:
                    max_index = num
        return max_index + 1

    def capture(self) -> None:
        self._ensure(self.screens)
        region = self._load_region()
        idx = self._next_index()
        out = self.screens / f"{idx:03d}.png"
        self._run("grim", "-g", region, str(out))
        self._notify(f"Saved screenshot: {out.name}")

    # ---------- OCR ----------
    def ocr_2_pdf(self):
        self._ensure(self.noalpha)
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
        images = sorted(self.noalpha.glob("*.png"))
        if not images:
            raise RuntimeError("No images found")
        tmp_pdf = self.base / "tmp.pdf"
        self._run("img2pdf", *map(str, images), "-o", str(tmp_pdf))
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
        for p in self.noalpha.glob("*"):
            p.unlink()
        self.noalpha.rmdir()
        self._notify(f"OCR saved: {self.output_pdf}")


def main():
    maimpdf_handler = MaimPdfTool()
    parser = argparse.ArgumentParser(prog="maimpdf")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("region")
    sub.add_parser("capture")
    sub.add_parser("ocr")
    args = parser.parse_args()
    match args.cmd:
        case "region":
            maimpdf_handler.select_region()
        case "capture":
            maimpdf_handler.capture()
        case "ocr":
            maimpdf_handler.ocr_2_pdf()


if __name__ == "__main__":
    main()
