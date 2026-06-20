#!/bin/bash

PROCESS_PATTERN="systemd-inhibit --what=handle-lid-switch"
PID=$(pgrep -f "$PROCESS_PATTERN")
if [ -n "$PID" ]; then
  kill "$PID"
  echo "[-] Sleep on lid-close RE-ENABLED (Normal behavior)."
else
  nohup systemd-inhibit --what=handle-lid-switch --why="Office Runner Toggle" --mode=block sleep infinity >/dev/null 2>&1 &
  echo "[+] Sleep on lid-close DISABLED (Laptop will stay awake)."
fi
