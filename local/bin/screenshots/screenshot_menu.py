#!/usr/bin/env python3
import argparse
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from PIL import Image


class ScreenshotManager:
    def __init__(self, storage_dir: Path, cache_dir: Path) -> None:
        self.storage_dir = storage_dir
        self.cache_dir = cache_dir
        # Ensure directories exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Sub-paths
        self.screens_dir = self.cache_dir / "screens"
        self.region_file = self.cache_dir / "region.txt"
        self.ocr_cache_png = self.cache_dir / "ocr_region.png"
        self.output_pdf = Path.home() / "Desktop" / "Documents" / "ocr_output.pdf"

    def _generate_path(self) -> Path:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return self.storage_dir / f"screenshot_{ts}.png"

    def _notify(self, msg: str, is_error: bool = False) -> None:
        title = "Screenshot Tool"
        urgency = "normal"
        if is_error:
            title = "Screenshot Tool Error"
            urgency = "critical"
        cmd = ["notify-send", "-u", urgency, title, msg]
        subprocess.run(cmd, check=False)

    def get_region(self) -> str:
        try:
            out = subprocess.check_output(["slurp"], stderr=subprocess.DEVNULL)
            region = out.decode().strip()
            return region
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    def copy_image_to_clipboard(self, img_path: Path) -> None:
        if not img_path.exists():
            return
        try:
            with img_path.open("rb") as f:
                cmd = ["wl-copy"]
                subprocess.run(cmd, input=f.read(), check=True)
            self._notify("Screenshot copied to clipboard!")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._notify("Failed to copy image to clipboard.", is_error=True)

    def capture(self, region: str) -> Path | None:
        file_path = self._generate_path()
        cmd = ["grim"]
        if region:
            cmd.extend(["-g", region])
        cmd.append(str(file_path))
        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return file_path
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._notify("Capture failed.", is_error=True)
            return

    def edit_image(self, file_path: Path) -> None:
        try:
            cmd = ["swappy", "-f", str(file_path)]
            subprocess.run(cmd, check=True)
        except FileNotFoundError:
            self._notify("Swappy not found. Image saved without edits.", is_error=True)

    def open_storage_folder(self) -> None:
        try:
            cmd = ["xdg-open", str(self.storage_dir)]
            subprocess.run(cmd, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._notify("Could not open file manager.", is_error=True)

    def handle_capture(self, is_region: bool, edit: bool) -> None:
        region_str = ""
        if is_region:
            region_str = self.get_region()
            if not region_str:
                return
        if not (file_path := self.capture(region_str)):
            return
        if edit:
            self.edit_image(file_path)
        else:
            self.copy_image_to_clipboard(file_path)

    def select_persistent_region(self) -> None:
        region = self.get_region()
        if not region:
            return
        self.region_file.write_text(region, encoding="utf-8")
        self._notify(f"Target region anchored: {region}")

    def _load_persistent_region(self) -> str:
        if not self.region_file.exists():
            self._notify("Region not found. Select region first.", is_error=True)
            raise RuntimeError()
        return self.region_file.read_text(encoding="utf-8").strip()

    def _next_index(self) -> int:
        self.screens_dir.mkdir(parents=True, exist_ok=True)
        pngs = sorted(self.screens_dir.glob("[0-9]*.png"))
        if not pngs:
            return 0
        last_png_num = int(pngs[-1].stem)
        return last_png_num + 1

    def capture_persistent_region(self) -> None:
        region = self._load_persistent_region()
        self.screens_dir.mkdir(parents=True, exist_ok=True)
        screen_path = self.screens_dir / f"{self._next_index():03d}.png"
        try:
            cmd = ["grim", "-g", region, str(screen_path)]
            subprocess.run(cmd, check=True)
            self._notify(f"Snippet saved to compilation queue: {screen_path.name}")
        except subprocess.CalledProcessError:
            self._notify("Failed capturing frozen region snapshot.", is_error=True)


class OCRProcessor:
    def __init__(self, manager: ScreenshotManager) -> None:
        self.manager = manager

    def extract_text_to_clipboard(self) -> None:
        region = self.manager.get_region()
        if not region:
            return
        try:
            cmd = ["grim", "-g", region, str(self.manager.ocr_cache_png)]
            subprocess.run(cmd, check=True)
            cmd = ["tesseract", str(self.manager.ocr_cache_png), "stdout", "-l", "eng"]
            text = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            ).stdout.strip()
            if text:
                cmd = ["wl-copy"]
                subprocess.run(cmd, input=text, text=True, check=True)
                self.manager._notify("Extracted text copied to clipboard!")
            else:
                self.manager._notify("OCR complete, but no text found.", is_error=True)
        except FileNotFoundError:
            self.manager._notify("Tesseract or Grim missing.", is_error=True)
        except subprocess.CalledProcessError:
            self.manager._notify("OCR engine failed.", is_error=True)
        finally:
            self.manager.ocr_cache_png.unlink(missing_ok=True)

    def compile_pdf(self) -> None:
        screenshots = sorted(self.manager.screens_dir.glob("*.png"))
        if not screenshots:
            self.manager._notify("No images found for PDF.", is_error=True)
            return
        tmp_pdf = self.manager.cache_dir / "tmp.pdf"
        try:
            # Flatten Alpha channels in-place to avoid disk duplication or mogrify subprocesses
            for img_path in screenshots:
                with Image.open(img_path) as img:
                    has_alpha = img.mode in ("RGBA", "LA")  # LA=greyscale
                    has_transparency = img.mode == "P" and "transparency" in img.info
                    if has_alpha or has_transparency:
                        # Create a solid white background & paste image onto it to drop alpha
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "RGBA":
                            mask = img.split()[-1]
                        background.paste(img, mask=mask)
                        background.save(img_path, "PNG")
            # Compile straightened images to standard structural PDF container
            cmd = ["img2pdf", *map(str, screenshots), "-o", str(tmp_pdf)]
            subprocess.run(cmd, check=True)
            self.manager.output_pdf.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                "ocrmypdf",
                "--language",
                "eng",
                "--output-type",
                "pdf",
                "--jpeg-quality",
                "100",
                str(tmp_pdf),
                str(self.manager.output_pdf),
            ]
            subprocess.run(cmd, check=True)
            self.manager._notify(f"OCR Pdf generated: {self.manager.output_pdf.name}")
            for img in screenshots:
                img.unlink()
        except FileNotFoundError:
            self.manager._notify("Missing (img2pdf/ocrmypdf).", is_error=True)
        except subprocess.CalledProcessError:
            self.manager._notify("PDF conversion failed.", is_error=True)
        finally:
            tmp_pdf.unlink(missing_ok=True)


class ScreenshotApp:
    menu_layout = [
        "󰹑 Screenshots",
        "Full Screen → Copy",
        "Full Screen → Edit",
        "Region → Copy",
        "Region → Edit",
        "",
        "󱄺 OCR Text",
        "Region → Clipboard",
        "",
        " OCR PDF",
        "Set Target Region",
        "Snapshot Region",
        "Compile to PDF",
        "",
        "Open Screenshots Folder",
        "Cancel",
    ]
    config_path = Path.home() / ".config" / "fuzzel" / "waybar.ini"

    def __init__(self, manager: ScreenshotManager, ocr: OCRProcessor) -> None:
        self.manager = manager
        self.ocr = ocr

    def execute_choice(self, choice: str) -> None:
        if choice == "Full Screen → Copy":
            self.manager.handle_capture(is_region=False, edit=False)
        elif choice == "Full Screen → Edit":
            self.manager.handle_capture(is_region=False, edit=True)
        elif choice == "Region → Copy":
            self.manager.handle_capture(is_region=True, edit=False)
        elif choice == "Region → Edit":
            self.manager.handle_capture(is_region=True, edit=True)
        elif choice == "Region → Clipboard":
            self.ocr.extract_text_to_clipboard()
        elif choice == "Freeze Target Region":
            self.manager.select_persistent_region()
        elif choice == "Snapshot Target Region":
            self.manager.capture_persistent_region()
        elif choice == "Compile Snippets to PDF":
            self.ocr.compile_pdf()
        elif choice == "Open Screenshots Folder":
            self.manager.open_storage_folder()

    def run(self) -> None:
        cmd = [
            "fuzzel",
            "--dmenu",
            "--hide-prompt",
            f"--lines={len(self.menu_layout)}",
            f"--width={max(len(x) for x in self.menu_layout)}",
            f"--config={self.config_path}",
        ]
        menu_str = "\n".join(self.menu_layout)
        try:
            result = subprocess.run(
                cmd, input=menu_str.encode(), stdout=subprocess.PIPE, check=True
            )
            choice = result.stdout.decode().strip()
            self.execute_choice(choice)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass


def main() -> None:
    storage_dir = Path.home() / "Desktop" / "Pictures" / "Screenshots"
    cache_dir = Path.home() / ".cache" / "screenshot_tool"
    manager = ScreenshotManager(storage_dir, cache_dir)
    ocr = OCRProcessor(manager)
    worker_actions = {
        "region": manager.select_persistent_region,
        "capture": manager.capture_persistent_region,
        "ocr": ocr.compile_pdf,
    }
    parser = argparse.ArgumentParser(
        description="Unified Wayland Screenshot & OCR Utility Interface"
    )
    parser.add_argument(
        "--worker-mode",
        choices=list(worker_actions.keys()),
        help="Internal routing tag execution handling specific sub-process worker actions.",
    )
    args = parser.parse_args()
    if args.worker_mode:
        worker_actions[args.worker_mode]()
        sys.exit(0)
    app = ScreenshotApp(manager, ocr)
    app.run()


if __name__ == "__main__":
    main()
