#!/usr/bin/env python3
import time
import subprocess
import json
import html
from pathlib import Path

TOOLTIP_FUNCTIONS = "\nLeft: Pavucontrol\t\nRight: Pause/Play\t\nMiddle: Rmpc\t"
ICONS_MAP = [(0, "󰝟"), (29, "󰕿"), (64, "󰖀"), (100, "󰕾")]
SEPERATOR = "  "


def playerctl_info(cmd) -> str:
    full_cmd = ["playerctl"] + cmd
    return subprocess.run(full_cmd, capture_output=True, text=True).stdout.strip()


def get_active_player(excluded: list[str]) -> str:
    running_player = ""
    data = playerctl_info(["-l"]).splitlines()
    for player in data:
        if player == "No players found":
            return ""
        if player in excluded:
            continue
        status = playerctl_info(["--player", player, "status"])
        if status == "Playing":
            running_player = player
    return running_player


def window_len(
    text_len: int,
    min_len: int = 8,
    max_len: int = 14,
    div: int = 3,
) -> int:
    value = text_len // div
    return max(min_len, min(value, max_len))


def get_metadata(player: str) -> str:
    cmd = ["--player", player, "metadata", "xesam:artist"]
    artist = playerctl_info(cmd)
    cmd = ["--player", player, "metadata", "xesam:title"]
    title = playerctl_info(cmd)
    return f"{artist} – {title}" if artist else title


def load_state(cache_file: Path) -> tuple[str, int, int]:
    try:
        data = json.loads(cache_file.read_text())
        track = data.get("track", "")
        position = data.get("pos", 0)
        timestamp = data.get("ts", int(time.time()))
        return (track, position, timestamp)
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
        return ("", 0, int(time.time()))


def save_state(
    cache_file: Path,
    track: str,
    pos: int,
) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    audio_dict = {"track": track, "pos": pos, "ts": time.time()}
    cache_file.write_text(json.dumps(audio_dict))


def scroll_text(
    win_length: int,
    text: str,
    position: float,
    delta: int,
    seperator: str,
) -> tuple[float, str]:
    if len(text) <= win_length:
        return 0.0, text[:win_length]
    full_text = text + seperator
    pos = (position + delta) % len(full_text)
    start = int(pos)
    return pos, (full_text * 2)[start : start + win_length]


def get_volume_icon(volume_icons: list[tuple[int, str]]) -> tuple[int, str]:
    cmd = ["pactl", "get-sink-volume", "@DEFAULT_SINK@"]
    out = subprocess.check_output(cmd, text=True).split("/")
    left_vol = int(out[1].strip().split("%")[0])
    right_vol = int(out[3].strip().split("%")[0])
    vol = (left_vol + right_vol) // 2
    for max_vol, icon in volume_icons:
        if vol <= max_vol:
            return vol, icon
    return vol, "󰕾"


def print_waybar(
    text: str,
    tooltip: str,
    waybar_class: str,
) -> None:
    dict = {
        "text": text,
        "tooltip": tooltip,
        "class": waybar_class,
    }
    print(json.dumps(dict, ensure_ascii=False))


def main():
    vol, icon = get_volume_icon(ICONS_MAP)
    if active_player := get_active_player(["JBL_Go_4"]):
        track = get_metadata(active_player)
        cache_file = Path.home() / ".cache" / "pulse_scroll" / "nowplaying_scroll.json"
        saved_track, saved_pos, saved_ts = load_state(cache_file)
        win_length = window_len(len(track))
        if track != saved_track:
            pos = 0.0
            display = track[:win_length]
        else:
            now = time.time()
            extra_d = 0
            delta = int(now - saved_ts) + extra_d
            pos, display = scroll_text(
                win_length=win_length,
                text=track,
                position=saved_pos,
                delta=delta,
                seperator=SEPERATOR,
            )
        print_waybar(
            f"{icon}<span size='4pt'> </span><span size='9pt'>{html.escape(display)}</span>",
            f"󰕾 {vol}%\n󰐊 {html.escape(track)}\t\n{TOOLTIP_FUNCTIONS}",
            "playing",
        )
        save_state(cache_file, track, int(pos))
    else:
        print_waybar(
            icon,
            f"󰕾 {vol}%\t\n{TOOLTIP_FUNCTIONS}",
            "stopped",
        )


if __name__ == "__main__":
    main()
