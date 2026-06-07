#!/usr/bin/env bash
TOOLTIP="Steam is running"
if pgrep -x "steam" >/dev/null; then
  printf '{"text":"%s","tooltip":"%s"}\n' "" "$TOOLTIP"
fi
