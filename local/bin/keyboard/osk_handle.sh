#!/bin/bash

CACHE_FILE="$HOME/.cache/wvkbd-deskintl_last_signal"
main() {
  if ! systemctl --user is-active --quiet wvkbd-deskintl.service; then
    systemctl --user start wvkbd-deskintl.service
    echo 1 >"$CACHE_FILE"
  fi
  last_signal=$(cat "$CACHE_FILE" 2>/dev/null || echo 2)
  new_signal=2
  if [[ "$last_signal" -eq 2 ]]; then
    new_signal=1
  fi
  pkill -SIGUSR"$new_signal" wvkbd-deskintl
  echo "$new_signal" >"$CACHE_FILE"
}
main
