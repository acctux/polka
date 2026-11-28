#!/usr/bin/env python3

import re
import subprocess
import asyncio
import html
import json
import time
from pathlib import Path

from dbus_fast import BusType
from dbus_fast.aio import MessageBus
from dbus_fast.constants import MessageType
from dbus_fast.message import Message


TOOLTIP_FUNCTIONS = "\nLeft: Wiremix\t\nRight: Pause/Play\t\nMiddle: Rmpc\t"
ICONS_MAP = {
    0: "󰝟",
    29: "󰕿",
    64: "󰖀",
    100: "󰕾",
}
DEFAULT_ICON = "󰕾"
SEPARATOR = "  "
EXCLUDED_PLAYERS = {"JBL_Go_4"}

CACHE_FILE = Path.home() / ".cache" / "pulse_scroll" / "nowplaying_scroll.json"


def unwrap(value):
    while hasattr(value, "value"):
        value = value.value
    return value


async def get_active_track() -> str:
    bus = await MessageBus(bus_type=BusType.SESSION).connect()

    try:
        reply = await bus.call(
            Message(
                destination="org.freedesktop.DBus",
                path="/org/freedesktop/DBus",
                interface="org.freedesktop.DBus",
                member="ListNames",
            )
        )
        if reply.message_type == MessageType.ERROR:
            return ""

        players = sorted(
            name
            for name in reply.body[0]
            if name.startswith("org.mpris.MediaPlayer2.")
            and name.removeprefix("org.mpris.MediaPlayer2.") not in EXCLUDED_PLAYERS
        )

        for player in players:
            reply = await bus.call(
                Message(
                    destination=player,
                    path="/org/mpris/MediaPlayer2",
                    interface="org.freedesktop.DBus.Properties",
                    member="GetAll",
                    signature="s",
                    body=["org.mpris.MediaPlayer2.Player"],
                )
            )
            if reply.message_type == MessageType.ERROR:
                continue

            props = {key: unwrap(value) for key, value in reply.body[0].items()}
            if props.get("PlaybackStatus") != "Playing":
                continue

            metadata = props.get("Metadata", {})
            artist = unwrap(metadata.get("xesam:artist", []))
            title = unwrap(metadata.get("xesam:title", ""))

            if isinstance(artist, (list, tuple)):
                artist = ", ".join(map(str, artist))

            return f"{artist} – {title}" if artist and title else str(artist or title)

        return ""
    finally:
        bus.disconnect()


def get_track() -> str:
    try:
        return asyncio.run(get_active_track())
    except (OSError, RuntimeError):
        return ""


def window_len(
    text_len: int,
    min_len: int = 8,
    max_len: int = 14,
    div: int = 3,
) -> int:
    return max(min_len, min(text_len // div, max_len))


def load_state(cache_file: Path) -> tuple[str, float, float]:
    try:
        data = json.loads(cache_file.read_text())
        return (
            str(data.get("track", "")),
            float(data.get("pos", 0)),
            float(data.get("ts", time.time())),
        )
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return "", 0.0, time.time()


def save_state(cache_file: Path, track: str, pos: float) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(
        json.dumps(
            {
                "track": track,
                "pos": pos,
                "ts": time.time(),
            }
        )
    )


def scroll_text(
    win_length: int,
    text: str,
    position: float,
    delta: int,
    separator: str,
) -> tuple[float, str]:
    if len(text) <= win_length:
        return 0.0, text

    full_text = text + separator
    pos = (position + delta) % len(full_text)
    start = int(pos)
    return pos, (full_text * 2)[start : start + win_length]


def get_volume_icon(volume_icons: dict[int, str]) -> tuple[int, str]:
    try:
        output = subprocess.run(
            ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        values = [int(value) for value in re.findall(r"(\d+)%", output)]
        if not values:
            return 0, DEFAULT_ICON

        volume = sum(values) // len(values)
        icon = next(
            (icon for limit, icon in volume_icons.items() if volume <= limit),
            DEFAULT_ICON,
        )
        return volume, icon
    except OSError:
        return 0, DEFAULT_ICON


def print_waybar(text: str, tooltip: str, waybar_class: str) -> None:
    print(
        json.dumps(
            {
                "text": text,
                "tooltip": tooltip,
                "class": waybar_class,
            },
            ensure_ascii=False,
        )
    )


def main() -> None:
    volume, icon = get_volume_icon(ICONS_MAP)
    track = get_track()

    if not track:
        print_waybar(icon, f"󰕾 {volume}%\t\n{TOOLTIP_FUNCTIONS}", "stopped")
        return

    saved_track, saved_pos, saved_ts = load_state(CACHE_FILE)
    win_length = window_len(len(track))

    if track == saved_track:
        pos, display = scroll_text(
            win_length=win_length,
            text=track,
            position=saved_pos,
            delta=int(time.time() - saved_ts),
            separator=SEPARATOR,
        )
    else:
        pos, display = 0.0, track[:win_length]

    print_waybar(
        f"{icon}<span size='4pt'> </span>"
        f"<span size='9pt'>{html.escape(display)}</span>",
        f"󰕾 {volume}%\n󰐊 {html.escape(track)}\t\n{TOOLTIP_FUNCTIONS}",
        "playing",
    )
    save_state(CACHE_FILE, track, pos)


if __name__ == "__main__":
    main()
