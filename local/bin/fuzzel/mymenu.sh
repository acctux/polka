#!/usr/bin/env bash

CHOICE_1="OCR Screenshot"
CHOICE_2="Set Screenshot Region"
CHOICE_3="Screenshot Folder"
CHOICE_4="Mount GoCrypt"

MENU="$CHOICE_1
$CHOICE_2
$CHOICE_3
$CHOICE_4
Cancel"

CHOICE=$(printf "%s\n" "$MENU" | fuzzel --dmenu --lines=6 --width=20 --hide-prompt --prompt="OCR Action:")

case "$CHOICE" in
"$CHOICE_1")
  $HOME/.local/bin/ocr/ocrcopy.py
  ;;
"$CHOICE_2")
  $HOME/Polka/local/bin/ocr/maimregion.sh
  ;;
"$CHOICE_3")
  nemo $HOME/Polka/local/bin/maimpdf/screens
  ;;
"$CHOICE_4")
  $HOME/.local/bin/folders/mountencrypted.sh
  ;;
"Cancel" | "")
  exit 0
  ;;
esac
