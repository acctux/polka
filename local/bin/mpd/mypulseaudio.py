#!/usr/bin/env python3
import subprocess
import json
import time
import html
from pathlib import Path

CACHE_FILE = Path.home() / ".cache" / "nowplaying_scroll.json"
SLEEP = 1
SCROLL_SPEED = 1
SEP = "  "
EXCLUDED = {"JBL_Go_4"}
DIV = 4
MIN_LEN = 6
MAX_LEN = 12
TOOLTIP_FUNCTIONS = "\nLeft: Pavucontrol\t\nRight: Pause/Play\t\nMiddle: Rmpc\t"


def run(cmd):
    return subprocess.run(
        ["playerctl"] + cmd, capture_output=True, text=True
    ).stdout.strip()


def get_players():
    return [p for p in run(["-l"]).splitlines() if p != "No players found"]


def get_active_player():
    players = get_players()
    for p in players:
        if p in EXCLUDED:
            continue
        status = run(["--player", p, "status"])
        if status == "Playing":
            return p
    return None


def window_len(text_len):
    length = max(MIN_LEN, min(MAX_LEN, text_len))
    length = (length // DIV) * DIV
    return max(MIN_LEN, length)


def get_metadata(player):
    artist = run(["--player", player, "metadata", "xesam:artist"])
    title = run(["--player", player, "metadata", "xesam:title"])
    return f"{artist} – {title}" if artist else title


def load_state():
    if CACHE_FILE.exists():
        data = json.loads(CACHE_FILE.read_text())
        return (
            data.get("track"),
            float(data.get("pos", 0)),
            data.get("ts", time.time()),
        )
    return None, 0.0, time.time()


def save_state(track, pos):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps({"track": track, "pos": pos, "ts": time.time()}))


def scroll_text(text, pos, delta):
    text_len = len(text)
    win = window_len(text_len)
    if text_len <= win:
        return 0.0, text[:win]
    cycle = text + SEP
    cycle_len = len(cycle)
    looped = cycle * 2
    pos = pos + delta * SCROLL_SPEED
    if pos >= cycle_len:
        pos -= cycle_len
    start = int(pos)
    return pos, looped[start : start + win]


def get_volume():
    out = subprocess.check_output(
        ["pactl", "get-sink-volume", "@DEFAULT_SINK@"], text=True
    )
    vols = [int(x) for x in __import__("re").findall(r"(\d+)%", out)]
    return sum(vols[:2]) // len(vols[:2]) if vols else 0


def volume_icon(vol):
    return "󰝟" if vol == 0 else "󰕿" if vol <= 29 else "󰖀" if vol <= 64 else "󰕾"


def main():
    while True:
        player = get_active_player()
        volume = get_volume()
        if not player:
            output = {
                "text": volume_icon(volume),
                "tooltip": f"󰕾 {volume}%\t\n{TOOLTIP_FUNCTIONS}",
                "class": "stopped",
            }
            print(json.dumps(output, ensure_ascii=False), flush=True)
            time.sleep(SLEEP)
            continue
        track = get_metadata(player)
        now = time.time()
        saved_track, saved_pos, saved_ts = load_state()
        if track != saved_track:
            pos = 0.0
            win = window_len(len(track))
            display = track[:win]
        else:
            pos, display = scroll_text(track, saved_pos, now - saved_ts)
        save_state(track, pos)
        safe_display = html.escape(display)
        text = f"{volume_icon(volume)}<span size='4pt'> </span><span size='9pt'>{safe_display}</span>"
        safe_track = html.escape(track)
        tooltip = f"󰕾 {volume}%\n󰐊 {safe_track}\t\n{TOOLTIP_FUNCTIONS}"
        print(
            json.dumps(
                {"text": text, "tooltip": tooltip, "class": "playing"},
                ensure_ascii=False,
            ),
            flush=True,
        )
        time.sleep(SLEEP)


if __name__ == "__main__":
    main()
