#!/bin/bash

CACHE="$HOME/.cache/wvkbd-deskintl_last_signal"
PID="$HOME/.cache/wvkbd-deskintl.pid"
if [[ ! -f $PID ]] || ! kill -0 "$(cat "$PID")" 2>/dev/null; then
  /usr/sbin/wvkbd-deskintl \
    -L 280 \
    --bg 101013 \
    --text F4F5F6 \
    --fg 191a1f \
    --fg-sp 1b1c21 \
    --press 0077ff \
    --press-sp 0077ff \
    --text-sp 33ccff \
    --alpha 220 \
    --landscape-layers full,cyrillic \
    &
  echo $! >"$PID"
  echo 1 >"$CACHE"
  exit
fi
last=$(cat "$CACHE" 2>/dev/null || echo 2)
sig=$((last == 2 ? 1 : 2))
kill -SIGUSR$sig "$(cat "$PID")"
echo $sig >"$CACHE"
