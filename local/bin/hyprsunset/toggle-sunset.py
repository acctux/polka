#!/usr/bin/env python3
from textwrap import dedent
import subprocess
from pathlib import Path

HOME = Path.home()
STATE_FILE = HOME / ".cache" / "hyprsunset_state"
PROFILES = [
    {"temperature": 1000, "gamma": 0.8},
    {"temperature": 2000, "gamma": 0.85},
    {"temperature": 8000, "gamma": 1.0},
]


def run_cmd(cmd: list[str], check=True):
    subprocess.run(cmd, check=check, text=True)


def restart_hyprsunset() -> None:
    try:
        run_cmd(["systemctl", "--user", "restart", "hyprsunset.service"])
    except subprocess.CalledProcessError:
        run_cmd(["pkill", "-f", "hyprsunset"], check=False)
        run_cmd(["systemctl", "--user", "stop", "hyprsunset.service"], check=False)
        run_cmd(["systemctl", "--user", "start", "hyprsunset.service"])


def render_config(profile: dict[str, float]) -> str:
    return dedent(
        f"""\
        max-gamma = 150

        profile {{
            temperature = {profile["temperature"]}
            gamma = {profile["gamma"]}
        }}
        """
    )


def main(
    state_file: Path = STATE_FILE, profile: list[dict[str, int | float]] = PROFILES
):
    sunset_conf = HOME / ".config" / "hypr" / "hyprsunset.conf"
    if state_file.exists():
        current = int(state_file.read_text().strip())
        state = (current + 1) % len(profile)
    else:
        state = 0
    config_text = render_config(profile[state])
    sunset_conf.write_text(config_text)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(str(state))
    restart_hyprsunset()
    print(f"Applied profile {state}: {profile[state]}")


if __name__ == "__main__":
    main()

