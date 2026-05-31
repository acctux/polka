#!/usr/bin/env python3
import time
import subprocess
import json
import html
from pathlib import Path

EXCLUDED = ["JBL_Go_4"]
TOOLTIP_FUNCTIONS = "\nLeft: Pavucontrol\t\nRight: Pause/Play\t\nMiddle: Rmpc\t"
CHAR_MOVE = 2


def run(cmd) -> str:
    return subprocess.run(
        ["playerctl"] + cmd, capture_output=True, text=True
    ).stdout.strip()


def get_active_player(excluded: list[str]) -> str:
    data = run(["-l"]).splitlines()
    running_player = ""
    for player in data:
        if player == "No players found":
            return ""
        if player in excluded:
            continue
        status = run(["--player", player, "status"])
        if status == "Playing":
            running_player = player
    return running_player


def window_len(text_len, min_len: int = 6, max_len: int = 12, div: int = 4) -> int:
    value = text_len // div
    if value < min_len:
        return min_len
    elif value > max_len:
        return max_len
    else:
        return value


def get_metadata(player) -> str:
    artist = run(["--player", player, "metadata", "xesam:artist"])
    title = run(["--player", player, "metadata", "xesam:title"])
    return f"{artist} – {title}" if artist else title


def load_state(cache_file: Path) -> tuple[str, int, int]:
    try:
        data = json.loads(cache_file.read_text())
        return (
            data.get("track", ""),
            data.get("pos", 0),
            data.get("ts", int(time.time())),
        )
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
        return ("", 0, int(time.time()))


def save_state(cache_file: Path, track: str, pos: int):
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps({"track": track, "pos": pos, "ts": time.time()}))


def scroll_text(
    text: str, pos: float, delta: int, sep: str = "  "
) -> tuple[float, str]:
    win = window_len(len(text))
    if len(text) <= win:
        return 0.0, text[:win]
    cycle = text + sep
    pos = (pos + delta) % len(cycle)
    start = int(pos)
    return pos, (cycle * 2)[start : start + win]


def get_volume_icon() -> tuple[int, str]:
    out = subprocess.check_output(
        ["pactl", "get-sink-volume", "@DEFAULT_SINK@"], text=True
    ).split("/")
    left_vol = int(out[1].strip().split("%")[0])
    right_vol = int(out[3].strip().split("%")[0])
    vol = int((left_vol + right_vol) / 2)
    icon = "󰕾"
    if vol == 0:
        icon = "󰝟"
    elif vol <= 29:
        icon = "󰕿"
    elif vol <= 64:
        icon = "󰖀"
    return (vol, icon)


def print_waybar(text: str, tooltip: str, waybar_class: str) -> None:
    dict = {"text": text, "tooltip": tooltip, "class": waybar_class}
    print(json.dumps(dict, ensure_ascii=False))


def run_player(vol: int, icon: str, active_player: str, cache_file: Path):
    track = get_metadata(active_player)
    saved_track, saved_pos, saved_ts = load_state(cache_file)
    if track != saved_track:
        pos = 0.0
        display = track[: window_len(len(track))]
    else:
        now = time.time()
        pos, display = scroll_text(track, saved_pos, int(now - saved_ts))
    print_waybar(
        f"{icon}<span size='4pt'> </span><span size='9pt'>{html.escape(display)}</span>",
        f"󰕾 {vol}%\n󰐊 {html.escape(track)}\t\n{TOOLTIP_FUNCTIONS}",
        "playing",
    )
    save_state(cache_file, track, int(pos))


def main():
    vol, icon = get_volume_icon()
    if active_player := get_active_player(EXCLUDED):
        run_player(
            vol,
            icon,
            active_player,
            Path.home() / ".cache" / "pulse_scroll" / "nowplaying_scroll.json",
        )
    else:
        print_waybar(icon, f"󰕾 {vol}%\t\n{TOOLTIP_FUNCTIONS}", "stopped")


if __name__ == "__main__":
    main()
