#!/usr/bin/env python3

import random
import subprocess
from pathlib import Path
import json
from wand.image import Image as WandImage
from wand.drawing import Drawing
from wand.color import Color

# ======================== Config ========================
HOME = Path.home()
CACHE_DIR = HOME / ".cache" / "wall"
WALL_SCRIPT_DIR = HOME / ".local" / "bin" / "wall"
WALL_IMG_DIR = WALL_SCRIPT_DIR / "wallpapers"
QUOTES_FILE = WALL_SCRIPT_DIR / "quotes.txt"
WALL_CACHE_JSON = CACHE_DIR / "last_used.json"
RESIZED_WALL = CACHE_DIR / "wallpaper_with_quote.png"
FONT_PATH = "/usr/share/fonts/OTF/FiraMonoNerdFont-Medium.otf"
FONT_SIZE = 11
TEXT_COLOR = Color("rgba(229, 231, 235, 0.65)")
SHADOW_COLOR = Color("rgba(16, 16, 19, 1)")
BOTTOM_PADDING = 1370
SIDE_PADDING = 0
TRANSITION_DURATION = 5
transition_type = [
    # "--transition-type",
    # "wipe",
]


def load_cache(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def save_cache(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def random_wallpaper(image_dir: Path, cache: dict) -> Path | None:
    images = [
        p
        for p in image_dir.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ]
    if not images:
        return None
    last = cache.get("last_wallpaper", "")
    selected = random.choice([p for p in images if str(p) != last] or images)
    cache["last_wallpaper"] = str(selected)
    return selected


def random_quote(quote_file: Path, cache: dict) -> str:
    quotes = [q.strip() for q in quote_file.read_text().splitlines() if q.strip()]
    if not quotes:
        return ""
    last = cache.get("last_quote", "")
    quote = random.choice([q for q in quotes if q != last] or quotes)
    cache["last_quote"] = quote
    return quote


def resize_to_screen(input_path: Path, output_path: Path) -> int:
    data = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"], text=True))
    screen_h: int = data[0]["height"]
    screen_w: int = data[0]["width"]
    hz: float = data[0]["refreshRate"]
    with WandImage(filename=str(input_path)) as img:
        img.transform(resize=f"{data[0]['width']}x{data[0]['height']}^")
        img.crop(
            left=max((img.width - data[0]["width"]) // 2, 0),
            top=max((img.height - screen_h) // 2, 0),
            width=screen_w,
            height=screen_h,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(filename=str(output_path))
    return int(hz)


def add_quote_with_wand(
    image_path: Path,
    quote: str,
    bottom_padding: int,
    font_path: str,
    font_size: int,
    shadow_color: Color,
    text_color: Color,
) -> None:

    with WandImage(filename=str(image_path)) as img:
        text_x = img.width // 2
        text_y = (img.height - bottom_padding + 200) // 2
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
            # Blur the shadow
            shadow_img.gaussian_blur(radius=0, sigma=1.5)
            # Composite shadow onto main image
            img.composite(shadow_img, 0, 0)
        # ---------------- Main text ----------------
        with Drawing() as draw:
            draw.font = font_path
            draw.font_size = font_size
            draw.fill_color = text_color
            draw.text_alignment = "center"
            draw.gravity = "center"
            draw.text(text_x, text_y, quote)
            draw(img)
        image_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(filename=str(image_path))


def set_wallpaper(
    image_path: Path, transition_hz: int, transition_duration: float
) -> None:
    try:
        subprocess.run(
            [
                "awww",
                "img",
                str(image_path),
                "--transition-duration",
                str(transition_duration),
                "--transition-fps",
                str(transition_hz),
            ]
            + transition_type,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"{e}")


# ====================== Main ======================
def main():
    cache = load_cache(WALL_CACHE_JSON)
    cache.setdefault("last_wallpaper", "")
    cache.setdefault("last_quote", "")
    wallpaper = random_wallpaper(WALL_IMG_DIR, cache)
    quote = random_quote(QUOTES_FILE, cache)
    save_cache(WALL_CACHE_JSON, cache)
    if not wallpaper or not quote:
        return
    hz = resize_to_screen(wallpaper, RESIZED_WALL)
    add_quote_with_wand(
        RESIZED_WALL,
        quote,
        BOTTOM_PADDING,
        FONT_PATH,
        FONT_SIZE,
        SHADOW_COLOR,
        TEXT_COLOR,
    )
    set_wallpaper(RESIZED_WALL, hz, TRANSITION_DURATION)


main()
