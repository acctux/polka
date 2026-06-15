#!/usr/bin/env python3

import yaml
import random
import subprocess
from pathlib import Path
import json
from wand.image import Image as WandImage
from wand.drawing import Drawing
from wand.color import Color
from dataclasses import dataclass

HOME = Path.home()
CACHE_DIR = HOME / ".cache" / "wall"
WALL_SCRIPT_DIR = HOME / ".local" / "bin" / "wall"
WALL_IMG_DIR = WALL_SCRIPT_DIR / "wallpapers"
QUOTES_FILE = Path("/home/nick/Lit/Docs/secdots/local/bin/wall/quotes.yaml")
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


@dataclass
class Quote:
    text: str
    author: str
    controversial: bool = False


def load_quotes_from_yaml(file_path: Path) -> list[Quote]:
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f) or []
    quotes = []
    for item in raw_data:
        if isinstance(item, dict):
            try:
                quotes.append(Quote(**item))
            except TypeError:
                continue
        elif isinstance(item, str):
            quotes.append(Quote(text=item, author="Unknown"))
    return quotes


def load_cache(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def save_cache(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def random_wallpaper(image_dir: Path, cache: dict) -> Path | None:
    if not image_dir.exists():
        return None
    images = []
    last = cache.get("last_wallpaper", "")
    for p in image_dir.iterdir():
        if str(p) == last:
            continue
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            images.append(p)
    selected = random.choice(images)
    cache["last_wallpaper"] = str(selected)
    return selected


def random_quote(quotes: list[Quote], cache: dict[str, str]) -> Quote | None:
    if not quotes:
        return None
    last_text = cache.get("last_quote_text", "")
    available_quotes = []
    for quote in quotes:
        if quote.text == last_text:
            continue
        available_quotes.append(quote)
    selected_quote = random.choice(available_quotes)
    cache["last_quote_text"] = selected_quote.text
    return selected_quote


def resize_to_screen(input_path: Path, output_path: Path) -> int:
    cmd = ["hyprctl", "monitors", "-j"]
    data = json.loads(subprocess.check_output(cmd, text=True))
    screen_h: int = data[0]["height"]
    screen_w: int = data[0]["width"]
    hz: float = data[0]["refreshRate"]
    with WandImage(filename=str(input_path)) as img:
        img.transform(resize=f"{data[0]['width']}x{data[0]['height']}^")
        left_crop = max((img.width - data[0]["width"]) // 2, 0)
        top_crop = max((img.height - screen_h) // 2, 0)
        img.crop(left=left_crop, top=top_crop, width=screen_w, height=screen_h)
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
                shadow_draw.text(text_x, text_y, quote)
                shadow_draw(shadow_img)
            shadow_img.gaussian_blur(radius=0, sigma=1.5)
            img.composite(shadow_img, 0, 0)
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
        cmd = [
            "awww",
            "img",
            str(image_path),
            "--transition-duration",
            str(transition_duration),
            "--transition-fps",
            str(transition_hz),
        ] + transition_type
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"{e}")


def main():
    cache = load_cache(WALL_CACHE_JSON)
    cache.setdefault("last_wallpaper", "")
    cache.setdefault("last_quote_text", "")
    wallpaper = random_wallpaper(WALL_IMG_DIR, cache)
    all_quotes = load_quotes_from_yaml(QUOTES_FILE)
    selected_quote_obj = random_quote(all_quotes, cache)
    save_cache(WALL_CACHE_JSON, cache)
    if not wallpaper or not selected_quote_obj:
        print("Missing wallpaper or quote records. Exiting.")
        return
    hz = resize_to_screen(wallpaper, RESIZED_WALL)
    formatted_quote_str = f'"{selected_quote_obj.text}" — {selected_quote_obj.author}'
    add_quote_with_wand(
        RESIZED_WALL,
        formatted_quote_str,
        BOTTOM_PADDING,
        FONT_PATH,
        FONT_SIZE,
        SHADOW_COLOR,
        TEXT_COLOR,
    )
    set_wallpaper(RESIZED_WALL, hz, TRANSITION_DURATION)


if __name__ == "__main__":
    main()
