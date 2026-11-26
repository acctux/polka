#!/usr/bin/env python3

import subprocess
from pathlib import Path

CACHE_FILE = Path.home() / ".cache" / "pulse_scroll" / "player.txt"
PLAYER_ORDER = ["mpd", "firefox.instance_1_71"]


def ctl(*args):
    return subprocess.run(
        ["playerctl", *args],
        capture_output=True,
        text=True,
        check=False,
    )


players = ctl("--list-all").stdout.splitlines()
ordered_players = [p for p in PLAYER_ORDER if p in players]
ordered_players += [p for p in players if p not in PLAYER_ORDER]

for player in ordered_players:
    if ctl("--player", player, "status").stdout.strip() == "Playing":
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(player)
        ctl("--player", player, "pause")
        break
else:
    if CACHE_FILE.exists():
        player = CACHE_FILE.read_text().strip()
        if player:
            ctl("--player", player, "play")
