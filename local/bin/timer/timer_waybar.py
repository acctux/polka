#!/usr/bin/env python3

import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------
STATE_FILE = Path.home() / ".cache" / "timer_state.json"


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# State cases — based on REAL current logic
# ----------------------------------------------------------------------
def case_no_timer() -> dict[str, Any]:
    return {"text": ""}


def case_running(state: dict) -> dict[str, Any]:
    start_time = datetime.fromisoformat(state["start_time"])
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    remaining = max(0, int(state["duration"] - elapsed))
    text = format_seconds(remaining)
    unit = load_state().get("unit")
    # Optional: flash when < 1 minute
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
        "alt": "timer",
    }


def case_paused(state: dict) -> dict[str, Any]:
    remaining = int(state["duration"])
    text = format_seconds(remaining)
    return {
        "text": f"⏸ {text}",
        "tooltip": f"Paused — {text} left",
        "class": "paused",
        "alt": "timer",
    }


def case_finished() -> dict[str, Any]:
    return {
        "text": "󰀨 DONE!",
        "tooltip": "Timer finished!",
        "class": "finished urgent",
        "alt": "timer",
    }


# ----------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------
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

    # Dispatch
    if not has_duration:
        output = case_no_timer()
    elif just_finished:
        output = case_finished()
    elif is_paused:
        output = case_paused(state)
    elif is_running_state:
        output = case_running(state)
    else:
        output = {"text": "Timer ?", "class": "error"}  # corrupted

    # Print only on change
    output_json = json.dumps(output)
    if output_json != last_output:
        print(output_json)
        sys.stdout.flush()
        last_output = output_json

    remaining = 0
    if is_running_state:
        elapsed = (
            datetime.now(timezone.utc) - datetime.fromisoformat(state["start_time"])
        ).total_seconds()
        remaining = max(0, int(state["duration"] - elapsed))
    sleep_time = 1
    time.sleep(sleep_time)
