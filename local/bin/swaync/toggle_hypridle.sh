#!/usr/bin/env bash
set +e

if systemctl --user is-active --quiet hypridle; then
  systemctl --user stop hypridle
  systemctl --user start lid-inhibit
  notify-send -u "critical" -a "swaync" "Hypridle" "The device won't suspend or sleep on close."
else
  systemctl --user start hypridle
  systemctl --user stop lid-inhibit
  notify-send -u "critical" -a "swaync" "Hypridle" "Hypridle and lid sleep reset."
fi

exit 0
