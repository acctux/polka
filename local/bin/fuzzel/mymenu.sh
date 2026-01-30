#!/usr/bin/env bash

CHOICE_1="OCR Screenshot"
CHOICE_2="Set Screenshot Region"
CHOICE_3="Screenshot Folder"
CHOICE_4="Start Youtube Daemon"
CHOICE_5="Stop Youtube Daemon"

MENU="$CHOICE_1
$CHOICE_2
$CHOICE_3
$CHOICE_4
$CHOICE_5
Cancel"

CHOICE=$(printf "%s\n" "$MENU" | fuzzel --dmenu --hide-prompt --prompt="OCR Action:")

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
"Cancel" | "")
  exit 0
  ;;
esac
