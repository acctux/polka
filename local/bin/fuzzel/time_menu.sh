#!/usr/bin/env bash

CHOICE_1="Set Timer"
CHOICE_2="Change Timezone"
CHOICE_3="Metric/Imperial"

MENU="$CHOICE_1
$CHOICE_2
$CHOICE_3
Cancel"
LINES=$(echo "$MENU" | wc -l)
CHOICE=$(printf "%s\n" "$MENU" | fuzzel --dmenu --hide-prompt --lines "$LINES" --config="$HOME/.config/fuzzel/timemenu.ini")
case "$CHOICE" in
"$CHOICE_1")
  python "$HOME/.local/bin/timer/set_timer.py"
  ;;
"$CHOICE_2")
  CURRENT_TZ=$(timedatectl show --property=Timezone --value)
  TZONE=$(timedatectl list-timezones | sort -u |
    fuzzel --dmenu --prompt="Timezone ($CURRENT_TZ): ")
  if [ -n "$TZONE" ]; then
    kitty sudo timedatectl set-timezone "$TZONE"
    pkill -SIGRTMIN+4 waybar
  fi
  ;;
"$CHOICE_3")
  python "$HOME/.local/bin/weather/main.py" --metric
  ;;
"Cancel" | "")
  exit 0
  ;;
esac
