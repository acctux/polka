#!/usr/bin/env python3

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import subprocess
import sys
import time


@dataclass
class TimerState:
    unit_idx: int = 1
    target: int = 0
    paused_rem: int = 0


class WaybarTimer:
    time_units = [("hour", "󱦟", 3600), ("minute", "󰔛", 60), ("second", "󰨀", 1)]

    def __init__(self, state: TimerState, state_file: Path) -> None:
        self.state = state
        self.state_file = state_file
        self._load()

    @staticmethod
    def format_time_left(secs: int) -> str:
        hours, remainder = divmod(max(0, secs), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def parse_duration(self, text: str) -> int:
        text = text.strip().lower()
        if ":" in text:
            parts = [int(x) for x in text.split(":") if x.isdigit()]
            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            if len(parts) == 2:
                return parts[0] * 60 + parts[1]
            return 0
        tokens = re.findall(r"(\d+)([hms]?)", text)
        if not tokens:
            return 0
        total_seconds = 0
        for value_str, unit in tokens:
            value = int(value_str)
            if unit == "h":
                total_seconds += value * 3600
            elif unit == "m":
                total_seconds += value * 60
            else:
                total_seconds += value
        return total_seconds

    def _load(self) -> None:
        if self.is_active():
            try:
                cfg = json.loads(self.state_file.read_text(encoding="utf-8"))
                self.state.unit_idx = int(cfg.get("unit_idx", 1)) % len(self.time_units)
                self.state.target = int(cfg.get("target", 0))
                self.state.paused_rem = int(cfg.get("paused_rem", 0))
                return
            except (json.JSONDecodeError, ValueError):
                pass
        self.state = TimerState()

    def save(self) -> None:
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(
                json.dumps(asdict(self.state), ensure_ascii=False), encoding="utf-8"
            )
        except OSError as err:
            sys.stderr.write(f"[Error]: Failed writing state: {err}\n")

    def is_active(self) -> bool:
        return self.state_file.exists()

    def clear(self) -> None:
        self.state_file.unlink(missing_ok=True)
        self.state = TimerState()

    def get_remaining(self) -> int:
        if self.state.paused_rem > 0:
            return self.state.paused_rem
        return max(0, self.state.target - int(time.time()))

    def start(self, text: str) -> None:
        total_seconds = self.parse_duration(text)
        if total_seconds > 0:
            self.state.target = int(time.time()) + total_seconds
            self.state.paused_rem = 0
            self._update_and_notify(f"Started—{self.format_time_left(total_seconds)}")
            self.save()

    def toggle_pause(self) -> None:
        rem = self.get_remaining()
        if rem <= 0:
            self.clear()
            self._update_and_notify("Timer Cleared.")
            return
        if self.state.paused_rem > 0:
            self.state.target = int(time.time()) + rem
            self.state.paused_rem = 0
            self._update_and_notify(f"Resumed — {self.format_time_left(rem)}")
        else:
            self.state.paused_rem = rem
            self.state.target = 0
            self._update_and_notify(f"Paused — {self.format_time_left(rem)}")
        self.save()

    def adjust(self, direction: int) -> None:
        remaining = self.get_remaining()
        sec_factor = self.time_units[self.state.unit_idx][2]
        new_rem = max(0, remaining + direction * sec_factor)
        if new_rem == 0:
            self._update_and_notify("Timer cleared.")
            self.clear()
        else:
            if self.state.paused_rem > 0:
                self.state.paused_rem = new_rem
            else:
                self.state.target = int(time.time()) + new_rem
            self.save()

    def cycle_unit(self) -> None:
        self.state.unit_idx = (self.state.unit_idx + 1) % len(self.time_units)
        if self.is_active():
            self.save()
        self._update_and_notify(
            f"Scroll Mode: {self.time_units[self.state.unit_idx][0]}"
        )

    def _update_and_notify(self, msg: str) -> None:
        try:
            cmd = ["notify-send", "-a", "Timer", "-i", "alarm-timer", msg]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            print(msg)

    def handle_waybar_output(self) -> None:
        if not self.is_active():
            print(json.dumps({"text": ""}))
            return
        rem = self.get_remaining()
        txt = self.format_time_left(rem)
        if self.state.paused_rem > 0:
            out, tooltip, cls = f"⏸ {txt}", f"Paused\nRemaining: {txt}\t", "paused"
        elif rem <= 0:
            out, tooltip, cls = "󰀨 DONE!", "Timer finished!", "finished"
            cmd = ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            out, tooltip, cls = (
                f"{self.time_units[self.state.unit_idx][1]} {txt}",
                f"Running\nRemaining: {txt}\t",
                "running",
            )
        print(
            json.dumps(
                {"text": out, "tooltip": tooltip, "class": cls}, ensure_ascii=False
            )
        )


def main() -> int:
    timer = WaybarTimer(TimerState(), Path.home() / ".cache" / "timer_state.json")
    parser = argparse.ArgumentParser(add_help=False)
    for opt in ["--status", "--stop", "--toggle", "--unit", "--up", "--down"]:
        parser.add_argument(opt, action="store_true")
    args, _ = parser.parse_known_args()
    if not timer.is_active() and any([args.stop, args.toggle, args.down]):
        return 0
    actions = [
        (args.status, timer.handle_waybar_output),
        (args.stop, timer.clear),
        (args.toggle, timer.toggle_pause),
        (args.unit, timer.cycle_unit),
        (args.up, lambda: timer.adjust(1)),
        (args.down, lambda: timer.adjust(-1)),
    ]
    for flag, action in actions:
        if flag:
            action()
            break
    else:
        cmd = [
            "zenity",
            "--entry",
            "--width=450",
            "--title=Timer",
            "--text=Duration (e.g., 25m, 1h30m, 90)",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            timer.start(res.stdout.strip())
        else:
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
