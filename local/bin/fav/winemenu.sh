#!/usr/bin/env bash

MENU=$'Create Wine Prefix\nRun Wine Exe\nCancel'

LINES=$(wc -l <<<"$MENU")
WIDTH=$(wc -L <<<"$MENU")

CHOICE=$(fuzzel --dmenu \
  --hide-prompt \
  --lines="$LINES" \
  --width="$WIDTH" \
  --config="$HOME/.config/fuzzel/fav-menu.ini" <<<"$MENU")

case "$CHOICE" in
"Create Wine Prefix") python "$HOME/Lit/polka/local/bin/wine/prefix.py" ;;
"Run Wine Exe") python "$HOME/Lit/polka/local/bin/wine/runwine.py" ;;
*) exit 0 ;;
esac
