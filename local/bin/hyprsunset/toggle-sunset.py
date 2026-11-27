#!/usr/bin/env python3

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Profile:
    temperature: int
    gamma: float


PROFILES = [
    Profile(
        temperature=1000,
        gamma=0.8,
    ),
    Profile(
        temperature=2000,
        gamma=0.85,
    ),
    Profile(
        temperature=8000,
        gamma=1.0,
    ),
]


def toggle_profile(lines: list[str]) -> Profile:
    in_profile = False
    current: dict[str, int | float] = {}
    value_lines: dict[str, int] = {}

    for index, line in enumerate(lines):
        text = line.strip()

        if text.startswith("profile") and "{" in text:
            in_profile = True
        elif in_profile and text == "}":
            break
        elif in_profile and "=" in text:
            key, value = (part.strip() for part in text.split("=", 1))
            if key in ("temperature", "gamma"):
                if key == "temperature":
                    current[key] = int(value)
                else:
                    current[key] = float(value)
                value_lines[key] = index

    existing = Profile(int(current["temperature"]), float(current["gamma"]))
    if existing in PROFILES:
        next_index = (PROFILES.index(existing) + 1) % len(PROFILES)
    else:
        next_index = 0
    profile = PROFILES[next_index]

    for key, value in (("temperature", profile.temperature), ("gamma", profile.gamma)):
        line_index = value_lines[key]
        indent = lines[line_index][
            : len(lines[line_index]) - len(lines[line_index].lstrip())
        ]
        lines[line_index] = f"{indent}{key} = {value}"

    return profile


def restart_service() -> None:
    try:
        subprocess.run(
            ["systemctl", "--user", "restart", "hyprsunset.service"],
            check=True,
        )
    except subprocess.CalledProcessError:
        subprocess.run(["pkill", "-f", "hyprsunset"], check=False)
        subprocess.run(
            ["systemctl", "--user", "stop", "hyprsunset.service"],
            check=False,
        )
        subprocess.run(
            ["systemctl", "--user", "start", "hyprsunset.service"],
            check=True,
        )


def main() -> None:
    sunset_conf = Path.home() / ".config" / "hypr" / "hyprsunset.conf"
    lines = sunset_conf.read_text().splitlines()
    profile = toggle_profile(lines)
    sunset_conf.write_text("\n".join(lines) + "\n")
    restart_service()
    print(f"Applied profile: {profile}")


if __name__ == "__main__":
    main()
