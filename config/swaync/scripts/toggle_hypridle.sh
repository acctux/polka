#!/usr/bin/env bash
set +e # disable immediate exit on error

if systemctl --user is-active --quiet hypridle; then
  systemctl --user stop hypridle
  notify-send -u "critical" -a "swaync" "Hypridle" "The device won't suspend"
else
  systemctl --user start hypridle
  notify-send -u "critical" -a "swaync" "Hypridle" "The device will suspend"
fi

exit 0
