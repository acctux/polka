#!/usr/bin/env bash
list="/run/wireguard/connections.list"
lines="$(grep -c . "$list")"
vpns=$(echo "$(<"$list")" && echo "Back")
choice=$(echo "$vpns" | fuzzel --dmenu \
  --hide-prompt \
  --lines "$((lines + 1))" \
  --config="$HOME/.config/fuzzel/vpnmenu.ini")
if [ -z "$choice" ]; then
  exit 0
fi
if [ "$choice" == "Back" ]; then
  "$HOME/.local/bin/fuzzel/network.sh"
else
  kitty sudo python "$HOME/.local/bin/protonvpn/protonconnect.py" "$choice"
fi
