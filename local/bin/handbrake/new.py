#!/usr/bin/env python3

import asyncio
import os
import sys
from dataclasses import dataclass
from urllib.parse import urlparse, unquote
from dbus_next.aio import MessageBus
from dbus_next import Message
from dbus_next.constants import MessageType


# =========================================================
# FILE URI HELPERS
# =========================================================
def uri_to_path(uri: str) -> str:
    if uri.startswith("file://"):
        uri = urlparse(uri).path
    return unquote(uri)


def unwrap(v):
    return v.value if hasattr(v, "value") else v


# =========================================================
# FILE PICKER (DESKTOP PORTAL VIA D-BUS)
# =========================================================
async def pick_file() -> str:
    future = asyncio.get_running_loop().create_future()
    bus = await MessageBus().connect()

    def handler(msg):
        try:
            if msg.message_type != MessageType.SIGNAL:
                return
            if msg.interface != "org.freedesktop.portal.Request":
                return
            if msg.member != "Response":
                return
            response_code, results = msg.body
            if response_code != 0:
                if not future.done():
                    future.set_result("")
                return
            uris = unwrap(results.get("uris", []))
            if not uris:
                if not future.done():
                    future.set_result("")
                return
            uri = unwrap(uris[0])
            path = uri_to_path(str(uri))
            if not future.done():
                future.set_result(path)
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
    except Exception as e:
        print(f"[!] D-Bus Portal Error: {e}", file=sys.stderr)
        return ""
    finally:
        bus.remove_message_handler(handler)


# =========================================================
# HANDBRAKE CONFIG STRUCT
# =========================================================
@dataclass(frozen=True)
class HandBrakeConfig:
    name: str
    quality: int
    encoder: str = "x264"
    format: str = "mp4"  # Corrected from "av_mp4" to standard "mp4"
    optimize: bool = True
    markers: bool = True
    audio_encoder: str = "aac"  # Corrected from "av_aac" to standard "aac"
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
        "Mobile Playback (H.265 / quality-24)", 24, encoder="x265", audio_bitrate=128
    ),
}


# =========================================================
# ZENITY MENUS
# =========================================================
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
        "TRUE",
        "WEB",
        PRESETS["WEB"].name,
        "FALSE",
        "FAST",
        PRESETS["FAST"].name,
        "FALSE",
        "YOUTUBE",
        PRESETS["YOUTUBE"].name,
        "FALSE",
        "ARCHIVE",
        PRESETS["ARCHIVE"].name,
        "FALSE",
        "MOBILE",
        PRESETS["MOBILE"].name,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
    )
    stdout, _ = await proc.communicate()
    selected_id = stdout.decode().strip()
    return PRESETS.get(selected_id)


# =========================================================
# HANDBRAKE INTERFACE
# =========================================================
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


# =========================================================
# MAIN EXECUTION
# =========================================================
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
