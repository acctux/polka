#!/usr/bin/env python3

import random
import subprocess
from pathlib import Path
import time
from wand.image import Image as WandImage
from wand.drawing import Drawing
from wand.color import Color

# ======================== Config ========================
HOME = Path.home()
CACHE_DIR = HOME / ".cache"
WALL_SCRIPT_DIR = HOME / ".local/bin/wall"
WALL_IMG_DIR = WALL_SCRIPT_DIR / "wallpapers"
QUOTES_FILE = WALL_SCRIPT_DIR / "quotes.txt"
FONT_PATH = "/usr/share/fonts/OTF/FiraMonoNerdFont-Medium.otf"
CACHE_FILE = CACHE_DIR / "wallpaper_with_quote.png"
LAST_WALL_FILE = CACHE_DIR / ".last_wallpaper"
TEMP_RESIZED = CACHE_DIR / "wallpaper_resized.png"
FONT_SIZE = 11
TEXT_COLOR = Color("rgba(229, 231, 235, 0.55)")
SHADOW_COLOR = Color("rgba(16, 16, 19, 1)")
BOTTOM_PADDING = 1250
SIDE_PADDING = 200
TRANSITION_DURATION = 4
screen_w = 1920
screen_h = 1080


# ====================== Functions ======================
def random_wallpaper(image_dir: Path, last_wall_file: Path) -> Path | None:
    if not image_dir.is_dir():
        return None
    images = [
        p
        for p in image_dir.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ]
    if not images:
        return None
    last = last_wall_file.read_text().strip() if last_wall_file.exists() else ""
    candidates = [p for p in images if str(p) != last] or images
    selected = random.choice(candidates)
    last_wall_file.parent.mkdir(parents=True, exist_ok=True)
    last_wall_file.write_text(str(selected))
    time.sleep(2)
    return selected


def resize_to_screen(image_path: Path, screen_w=1920, screen_h=1080) -> Path:
    with WandImage(filename=str(image_path)) as img:
        img.transform(resize=f"{screen_w}x{screen_h}^")
        img.crop(
            left=max((img.width - screen_w) // 2, 0),
            top=max((img.height - screen_h) // 2, 0),
            width=screen_w,
            height=screen_h,
        )
        TEMP_RESIZED.parent.mkdir(parents=True, exist_ok=True)
        img.save(filename=str(TEMP_RESIZED))
        time.sleep(10)
    return TEMP_RESIZED


def add_quote_with_wand(
    image_path: Path,
    side_padding: int = SIDE_PADDING,
    bottom_padding: int = BOTTOM_PADDING,
    font_path: str = FONT_PATH,
    font_size: int = FONT_SIZE,
    shadow_color: Color = SHADOW_COLOR,
    text_color: Color = TEXT_COLOR,
) -> Path:
    if not QUOTES_FILE.exists():
        quote = ""
    quotes = [
        line.strip() for line in QUOTES_FILE.read_text().splitlines() if line.strip()
    ]
    quote = random.choice(quotes) if quotes else ""
    with WandImage(filename=str(image_path)) as img:
        left, top = side_padding, 200
        box_width, box_height = (
            img.width - 2 * side_padding,
            img.height - bottom_padding - 200,
        )
        text_x = int(left + box_width / 2)
        text_y = int(top + box_height / 2)
        # ---------------- Shadow layer ----------------
        with WandImage(
            width=img.width,
            height=img.height,
            background=Color("transparent"),
        ) as shadow_img:
            with Drawing() as shadow_draw:
                shadow_draw.font = font_path
                shadow_draw.font_size = font_size
                shadow_draw.fill_color = shadow_color
                shadow_draw.text_alignment = "center"
                shadow_draw.gravity = "center"
                shadow_draw.text(
                    text_x,
                    text_y,
                    quote,
                )
                shadow_draw(shadow_img)
                time.sleep(2)
            # Blur the shadow
            shadow_img.gaussian_blur(radius=0, sigma=1.5)
            # Composite shadow onto main image
            img.composite(shadow_img, 0, 0)
            time.sleep(2)
        # ---------------- Main text ----------------
        with Drawing() as draw:
            draw.font = font_path
            draw.font_size = font_size
            draw.fill_color = text_color
            draw.text_alignment = "center"
            draw.gravity = "center"
            draw.text(text_x, text_y, quote)
            draw(img)
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        img.save(filename=str(CACHE_FILE))
    return CACHE_FILE


def set_wallpaper(
    image_path: Path, transition_duration: float = TRANSITION_DURATION
) -> bool:
    if not image_path.exists():
        return False
    try:
        subprocess.run(
            [
                "swww",
                "img",
                str(image_path),
                # "--transition-type",
                # "wipe",
                "--transition-duration",
                str(transition_duration),
                "--transition-fps",
                "144",
            ],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"{e}")
        return False


# ====================== Main ======================
def main():
    wallpaper = random_wallpaper(WALL_IMG_DIR, LAST_WALL_FILE)
    if not wallpaper:
        return
    resized_wp = resize_to_screen(wallpaper, screen_w, screen_h)
    final_image = add_quote_with_wand(
        resized_wp,
        SIDE_PADDING,
        BOTTOM_PADDING,
        FONT_PATH,
        FONT_SIZE,
        SHADOW_COLOR,
        TEXT_COLOR,
    )
    set_wallpaper(final_image)


if __name__ == "__main__":
    main()
