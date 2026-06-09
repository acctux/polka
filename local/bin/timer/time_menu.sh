#!/usr/bin/env bash

CHOICE_1="Calendar"
CHOICE_2="Set Timer"
CHOICE_3="Change Timezone"

MENU="$CHOICE_1
$CHOICE_2
$CHOICE_3
Cancel"

LINES=$(echo "$MENU" | wc -l)
CHOICE=$(printf "%s\n" "$MENU" | fuzzel --dmenu --hide-prompt --lines "$LINES" --config="$HOME/.config/fuzzel/waybar.ini" --anchor="top-left")

case "$CHOICE" in
"$CHOICE_1")
  kitty ikhal &
  ;;
"$CHOICE_2")
  "$HOME/.local/bin/timer/topwatch.py"
  ;;
"$CHOICE_3")
  CURRENT_TZ=$(timedatectl show --property=Timezone --value)
  TZONE=$(timedatectl list-timezones | sort -u |
    fuzzel --dmenu --prompt="Timezone ($CURRENT_TZ): ")
  if [ -n "$TZONE" ]; then
    sudo -A timedatectl set-timezone "$TZONE"
    pkill -SIGRTMIN+4 waybar
  fi
  ;;
"Cancel" | "")
  exit 0
  ;;
esac
