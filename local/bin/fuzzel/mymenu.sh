#!/usr/bin/env bash

CHOICE_1="OCR Screenshot"
CHOICE_2="Set Screenshot Region"
CHOICE_3="Mount GoCrypt"
CHOICE_4="Capture QR Code"

MENU="$CHOICE_1
$CHOICE_2
$CHOICE_3
$CHOICE_4
Cancel"

CHOICE=$(printf "%s\n" "$MENU" | fuzzel --dmenu --hide-prompt --config="$HOME/.config/fuzzel/fav-menu.ini")

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
"Cancel" | "")
  exit 0
  ;;
esac
