#!/usr/bin/env bash

CHOICE_1="OCR Screenshot"
CHOICE_2="Set Screenshot Region"
CHOICE_3="Mount GoCrypt"
CHOICE_4="Capture QR Code"
CHOICE_5="Create Wine Prefix"
CHOICE_6="Run Wine Exe"
CHOICE_7="Toggle Hz"
CHOICE_8="Toggle Game Mode"

MENU="$CHOICE_1
$CHOICE_2
$CHOICE_3
$CHOICE_4
$CHOICE_5
$CHOICE_6
$CHOICE_7
$CHOICE_8
Cancel"

LINE_COUNT=$(echo "$MENU" | wc -l)

CHOICE=$(printf "%s\n" "$MENU" | fuzzel --dmenu --hide-prompt --lines=$LINE_COUNT --config="$HOME/.config/fuzzel/fav-menu.ini")

case "$CHOICE" in
"$CHOICE_1")
  $HOME/.local/bin/ocr/ocrcopy.py
  ;;
"$CHOICE_2")
  $HOME/Polka/local/bin/ocr/maimregion.sh
  ;;
"$CHOICE_3")
  $HOME/.local/bin/folders/mountencrypted.sh
  ;;
"$CHOICE_4")
  $HOME/.local/bin/qr/qr.py
  ;;
"$CHOICE_5")
  python $HOME/Lit/polka/local/bin/wine/prefix.py
  ;;
"$CHOICE_6")
  python $HOME/Lit/polka/local/bin/wine/runwine.py
  ;;
"$CHOICE_7")
  python $HOME/Lit/polka/local/bin/power/hz.py
  ;;
"$CHOICE_8")
  python $HOME/Lit/polka/local/bin/power/gamemode.py
  ;;
"Cancel" | "")
  exit 0
  ;;
esac
