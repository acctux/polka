#!/usr/bin/env bash

MENU=$'Show WiFi QR\nScan QR\nCancel'
LINES=$(wc -l <<<"$MENU")
WIDTH=$(awk 'length > max { max = length } END { print max }' <<<"$MENU")
WIDTH=$((WIDTH + 1))
CHOICE=$(fuzzel --dmenu \
  --hide-prompt \
  --lines="$LINES" \
  --width="$WIDTH" \
  --config="$HOME/.config/fuzzel/fav-menu.ini" <<<"$MENU")

case "$CHOICE" in
"Show WiFi QR") kitty --hold /home/nick/Lit/polka/local/bin/qr/wifiqr.py ;;
"Scan QR") python /home/nick/Lit/polka/local/bin/qr/qr.py ;;
*) exit 0 ;;
esac
