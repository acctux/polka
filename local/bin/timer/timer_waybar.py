#!/usr/bin/env python3

import json
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

STATE_FILE = Path.home() / ".cache" / "timer_state.json"


def format_seconds(secs: int) -> str:
    secs = max(0, int(secs))
    h, r = divmod(secs, 3600)
    m, s = divmod(r, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def case_running(state: dict) -> dict[str, Any]:
    start_time = datetime.fromisoformat(state["start_time"])
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    remaining = max(0, int(state["duration"] - elapsed))
    text = format_seconds(remaining)
    unit = load_state().get("unit")
    if unit == "minutes":
        icon = "󰔛"
    elif unit == "hours":
        icon = "󱦟"
    else:
        icon = "󰨀"
    return {
        "text": f" {icon} {text} ",
        "tooltip": f"Running — {text} remaining{unit}",
        "class": f"{icon}",
    }


def case_paused(state: dict) -> dict[str, Any]:
    text = format_seconds(int(state["duration"]))
    return {
        "text": f"⏸ {text}",
        "tooltip": f"Paused — {text} left",
        "class": "paused",
    }


def case_finished() -> dict[str, Any]:
    subprocess.Popen(
        ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return {
        "text": "󰀨 DONE!",
        "tooltip": "Timer finished!",
        "class": "finished urgent",
    }


def main():
    last_output = None
    while True:
        state = load_state()
        has_duration = bool(state.get("duration"))
        is_paused = state.get("paused_at") is not None
        is_running_state = "start_time" in state and state.get("paused_at") is None
        just_finished = False
        if is_running_state:
            elapsed = (
                datetime.now(timezone.utc) - datetime.fromisoformat(state["start_time"])
            ).total_seconds()
            if elapsed >= state["duration"]:
                just_finished = True
        if not has_duration:
            output = {"text": ""}
        elif just_finished:
            output = case_finished()
        elif is_paused:
            output = case_paused(state)
        elif is_running_state:
            output = case_running(state)
        else:
            output = {"text": "Timer ?", "class": "error"}
        # Print only on change
        output_json = json.dumps(output)
        if output_json != last_output:
            print(output_json)
            sys.stdout.flush()
            last_output = output_json
        if is_running_state:
            elapsed = (
                datetime.now(timezone.utc) - datetime.fromisoformat(state["start_time"])
            ).total_seconds()
        sleep_time = 1
        time.sleep(sleep_time)


if __name__ == "__main__":
    main()
