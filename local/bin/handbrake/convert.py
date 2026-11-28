#!/usr/bin/env python3

import asyncio
import os
import sys
from dataclasses import dataclass
from urllib.parse import unquote, urlparse

from dbus_fast import Message
from dbus_fast.aio import MessageBus
from dbus_fast.constants import MessageType


def uri_to_path(uri: str) -> str:
    if uri.startswith("file://"):
        uri = urlparse(uri).path
    return unquote(uri)


def unwrap(value):
    return value.value if hasattr(value, "value") else value


async def pick_file() -> str:
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    bus = await MessageBus().connect()

    def handler(msg):
        if (
            msg.message_type != MessageType.SIGNAL
            or msg.interface != "org.freedesktop.portal.Request"
            or msg.member != "Response"
        ):
            return

        try:
            response_code, results = msg.body
            if response_code != 0:
                result = ""
            else:
                uris = unwrap(results.get("uris", []))
                result = uri_to_path(str(unwrap(uris[0]))) if uris else ""

            if not future.done():
                future.set_result(result)
        except Exception:
            if not future.done():
                future.set_result("")

    bus.add_message_handler(handler)

    try:
        await bus.call(
            Message(
                destination="org.freedesktop.portal.Desktop",
                path="/org/freedesktop/portal/desktop",
                interface="org.freedesktop.portal.FileChooser",
                member="OpenFile",
                signature="ssa{sv}",
                body=["", "Select video file", {}],
            )
        )
        return await future
    except Exception as exc:
        print(f"[!] D-Bus Portal Error: {exc}", file=sys.stderr)
        return ""
    finally:
        bus.remove_message_handler(handler)
        bus.disconnect()


@dataclass(frozen=True)
class HandBrakeConfig:
    name: str
    quality: int
    encoder: str = "x264"
    format: str = "mp4"
    optimize: bool = True
    markers: bool = True
    audio_encoder: str = "aac"
    audio_bitrate: int = 128


PRESETS = {
    "WEB": HandBrakeConfig("Web Optimized (H.264 / quality-23)", 23),
    "FAST": HandBrakeConfig(
        "Fast Encode (H.264 / quality-28)", 28, optimize=False, markers=False
    ),
    "YOUTUBE": HandBrakeConfig(
        "YouTube HQ (H.264 / quality-20)", 20, audio_bitrate=160
    ),
    "ARCHIVE": HandBrakeConfig(
        "Archive HQ (H.265 / quality-18)",
        18,
        encoder="x265",
        optimize=False,
        audio_bitrate=192,
    ),
    "MOBILE": HandBrakeConfig(
        "Mobile Playback (H.265 / quality-24)", 24, encoder="x265"
    ),
}


async def zenity_choose_preset() -> HandBrakeConfig | None:
    cmd = [
        "zenity",
        "--list",
        "--radiolist",
        "--title=HandBrake Config Options",
        "--text=Select a preset profile for encoding:",
        "--column=Select",
        "--column=ID",
        "--column=Description",
    ]

    for index, (preset_id, preset) in enumerate(PRESETS.items()):
        cmd.extend(["TRUE" if index == 0 else "FALSE", preset_id, preset.name])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await proc.communicate()
    return PRESETS.get(stdout.decode().strip())


def build_command(inp: str, out: str, cfg: HandBrakeConfig) -> list[str]:
    cmd = [
        "HandBrakeCLI",
        "-i",
        inp,
        "-o",
        out,
        "-e",
        cfg.encoder,
        "-f",
        cfg.format,
        "-q",
        str(cfg.quality),
        "-E",
        cfg.audio_encoder,
        "-B",
        str(cfg.audio_bitrate),
    ]
    if cfg.optimize:
        cmd.append("-O")
    if cfg.markers:
        cmd.append("-m")
    return cmd


async def run_handbrake(inp: str, cfg: HandBrakeConfig) -> str:
    out = os.path.splitext(inp)[0] + "_encoded.mp4"
    proc = await asyncio.create_subprocess_exec(*build_command(inp, out, cfg))
    await proc.communicate()
    return out


async def main():
    inp = await pick_file()
    if not inp:
        print("No file selected or transaction canceled.")
        return

    print("Selected File:", inp)
    cfg = await zenity_choose_preset()
    if not cfg:
        print("No preset profile selected.")
        return

    print(f"Selected Profile: {cfg.name}")
    print("Encoding started...")
    out = await run_handbrake(inp, cfg)
    print("Finished Processing:", out)


if __name__ == "__main__":
    asyncio.run(main())
