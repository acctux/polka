#!/usr/bin/env bash

CHOICE_1="Calendar"
CHOICE_2="Set Timer"
CHOICE_3="Change Timezone"

MENU="$CHOICE_1
$CHOICE_2
$CHOICE_3
Cancel"

LINES=$(echo "$MENU" | wc -l)

CHOICE=$(printf "%s\n" "$MENU" | fuzzel --dmenu --hide-prompt --lines "$LINES" --config="$HOME/.config/fuzzel/timemenu.ini")

case "$CHOICE" in
"$CHOICE_1")
  kitty ikhal &
  ;;
"$CHOICE_2")
  python "$HOME/.local/bin/timer/set_timer.py"
  ;;
"$CHOICE_3")
  CURRENT_TZ=$(timedatectl show --property=Timezone --value)
  TZONE=$(timedatectl list-timezones | sort -u |
    fuzzel --dmenu --prompt="Timezone ($CURRENT_TZ): ")
  if [ -n "$TZONE" ]; then
    kitty sudo timedatectl set-timezone "$TZONE"
    pkill -SIGRTMIN+4 waybar
  fi
  ;;
"Cancel" | "")
  exit 0
  ;;
esac
