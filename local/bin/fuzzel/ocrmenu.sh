#!/usr/bin/env bash

MENU=$'OCR Screenshot\nSet Screenshot Region\nCancel'

LINES=$(wc -l <<<"$MENU")
WIDTH=$(wc -L <<<"$MENU")

CHOICE=$(fuzzel --dmenu \
  --hide-prompt \
  --lines="$LINES" \
  --width="$WIDTH" \
  --config="$HOME/.config/fuzzel/fav-menu.ini" <<<"$MENU")

case "$CHOICE" in
"OCR Screenshot") python $HOME/.local/bin/ocr/ocrcopy.py ;;
"Set Screenshot Region") $HOME/Polka/local/bin/ocr/maimregion.sh ;;
*) exit 0 ;;
esac
