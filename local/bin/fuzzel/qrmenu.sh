#!/usr/bin/env bash

MENU=$'Show WiFi QR\nScan QR From Screenshot\nScan QR From Webcam\nCancel'
LINES=$(wc -l <<<"$MENU")
WIDTH=$(awk 'length > max { max = length } END { print max }' <<<"$MENU")
WIDTH=$((WIDTH + 2))

CHOICE=$(fuzzel --dmenu \
  --hide-prompt \
  --lines="$LINES" \
  --width="$WIDTH" \
  --config="$HOME/.config/fuzzel/fav-menu.ini" <<<"$MENU")

case "$CHOICE" in
"Show WiFi QR")
  kitty --hold /home/nick/Lit/polka/local/bin/qr/wifiqr.py
  ;;
"Scan QR From Screenshot")
  python /home/nick/Lit/polka/local/bin/qr/qr.py
  ;;
"Scan QR From Webcam")
  zbarcam-gtk
  ;;
*)
  exit 0
  ;;
esac
