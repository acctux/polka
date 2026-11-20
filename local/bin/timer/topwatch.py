#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

TIME_UNITS = (
    ("hour", "󱦟", 3600),
    ("minute", "󰔛", 60),
    ("second", "󰨀", 1),
)
STATE_FILE = Path.home() / ".cache" / "timer_state.json"


@dataclass
class TimerState:
    unit_idx: int = 1
    target: int = 0
    paused_rem: int = 0


def parse_duration(text: str) -> int:
    text = text.strip().lower()

    if ":" in text:
        parts = text.split(":")
        if not all(part.isdigit() for part in parts):
            return 0
        values = list(map(int, parts))
        if len(values) == 2:
            return values[0] * 60 + values[1]
        if len(values) == 3:
            return values[0] * 3600 + values[1] * 60 + values[2]
        return 0

    tokens = re.findall(r"(\d+)([hms]?)", text)
    if not tokens or "".join(value + unit for value, unit in tokens) != text:
        return 0

    multipliers = {"h": 3600, "m": 60, "s": 1, "": 1}
    return sum(int(value) * multipliers[unit] for value, unit in tokens)


def format_time_left(seconds: int) -> str:
    hours, remainder = divmod(max(0, seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


class WaybarTimer:
    def __init__(self, state_file: Path) -> None:
        self.state_file = state_file
        self.state = self._load()

    def _load(self) -> TimerState:
        try:
            config = json.loads(self.state_file.read_text(encoding="utf-8"))
            return TimerState(
                unit_idx=int(config.get("unit_idx", 1)) % len(TIME_UNITS),
                target=int(config.get("target", 0)),
                paused_rem=int(config.get("paused_rem", 0)),
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return TimerState()

    def save(self) -> None:
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(
                json.dumps(asdict(self.state), ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as error:
            print(f"[Error]: Failed writing state: {error}", file=sys.stderr)

    def clear(self) -> None:
        self.state_file.unlink(missing_ok=True)
        self.state = TimerState()

    def remaining(self) -> int:
        if self.state.paused_rem > 0:
            return self.state.paused_rem
        return max(0, self.state.target - int(time.time()))

    def notify(self, message: str) -> None:
        subprocess.run(
            ["notify-send", "-a", "Timer", "-i", "alarm-timer", message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    def start(self, text: str) -> None:
        seconds = parse_duration(text)
        if seconds <= 0:
            return

        self.state.target = int(time.time()) + seconds
        self.state.paused_rem = 0
        self.save()
        self.notify(f"Started—{format_time_left(seconds)}")

    def toggle_pause(self) -> None:
        seconds = self.remaining()
        if seconds <= 0:
            self.clear()
            self.notify("Timer Cleared.")
            return

        if self.state.paused_rem:
            self.state.target = int(time.time()) + seconds
            self.state.paused_rem = 0
            message = f"Resumed — {format_time_left(seconds)}"
        else:
            self.state.paused_rem = seconds
            self.state.target = 0
            message = f"Paused — {format_time_left(seconds)}"

        self.save()
        self.notify(message)

    def adjust(self, direction: int) -> None:
        seconds = max(
            0,
            self.remaining() + direction * TIME_UNITS[self.state.unit_idx][2],
        )

        if seconds == 0:
            self.clear()
            self.notify("Timer cleared.")
        elif self.state.paused_rem:
            self.state.paused_rem = seconds
            self.save()
        else:
            self.state.target = int(time.time()) + seconds
            self.save()

    def cycle_unit(self) -> None:
        self.state.unit_idx = (self.state.unit_idx + 1) % len(TIME_UNITS)
        if self.state_file.exists():
            self.save()
        self.notify(f"Scroll Mode: {TIME_UNITS[self.state.unit_idx][0]}")

    def print_status(self) -> None:
        if not self.state_file.exists():
            print(json.dumps({"text": ""}))
            return

        seconds = self.remaining()
        text = format_time_left(seconds)

        if self.state.paused_rem:
            result = {
                "text": f"⏸ {text}",
                "tooltip": f"Paused\nRemaining: {text}\t",
                "class": "paused",
            }
        elif seconds <= 0:
            result = {
                "text": "󰀨 DONE!",
                "tooltip": "Timer finished!",
                "class": "finished",
            }
            subprocess.Popen(
                ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            result = {
                "text": f"{TIME_UNITS[self.state.unit_idx][1]} {text}",
                "tooltip": f"Running\nRemaining: {text}\t",
                "class": "running",
            }

        print(json.dumps(result, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    for option in ("--status", "--stop", "--toggle", "--unit", "--up", "--down"):
        parser.add_argument(option, action="store_true")
    args, _ = parser.parse_known_args()

    timer = WaybarTimer(STATE_FILE)

    if not timer.state_file.exists() and (args.stop or args.toggle or args.down):
        return 0

    actions = (
        (args.status, timer.print_status),
        (args.stop, timer.clear),
        (args.toggle, timer.toggle_pause),
        (args.unit, timer.cycle_unit),
        (args.up, lambda: timer.adjust(1)),
        (args.down, lambda: timer.adjust(-1)),
    )

    for enabled, action in actions:
        if enabled:
            action()
            return 0

    result = subprocess.run(
        [
            "zenity",
            "--entry",
            "--width=450",
            "--title=Timer",
            "--text=Duration (e.g., 25m, 1h30m, 90)",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        timer.start(result.stdout.strip())

    return 0


if __name__ == "__main__":
    sys.exit(main())
