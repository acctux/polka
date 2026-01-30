#!/usr/bin/env bash

CHOICE_1="WiFi"
CHOICE_2="VPN"

while true; do
  MENU="$CHOICE_1
$CHOICE_2
Cancel"
  CHOICES=$(echo "$MENU" | wc -l)
  echo "Number of choices: $CHOICES"
  CHOICE=$(printf "%s\n" "$MENU" | fuzzel --dmenu --hide-prompt --lines=$CHOICES --config="$HOME/.config/fuzzel/vpnmenu.ini")
  case "$CHOICE" in
  "$CHOICE_1")
    python "$HOME/.local/bin/network/network.py"
    break
    ;;
  "$CHOICE_2")
    list="/run/wireguard/connections.list"
    lines="$(grep -c . "$list")"
    vpns=$(echo "$(<"$list")" && echo "Back")
    choice=$(echo "$vpns" | fuzzel --dmenu \
      --hide-prompt \
      --lines "$((lines + 1))" \
      --config="$HOME/.config/fuzzel/vpnmenu.ini")
    if [ -z "$choice" ]; then
      exit 1
    fi
    if [ "$choice" == "Back" ]; then
      continue
    else
      kitty sudo python "$HOME/.local/bin/protonvpn/protonconnect.py" "$choice"
      break
    fi
    ;;
  "Cancel" | "")
    exit 0
    ;;
  esac
done
