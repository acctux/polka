#!/usr/bin/env bash

launch_wifi() {
  if pgrep -x NetworkManager >/dev/null; then
    kitty nmtui
  elif pgrep -x iwd >/dev/null; then
    kitty impala
  else
    return 1
  fi
}

vpn_menu() {
  "$HOME/.local/bin/network/vpnmenu.py"
}

change_backend() {
  "$HOME/.local/bin/network/change_backend.py"
}

OPTIONS=(
  "Launch WiFi Manager::launch_wifi"
  "VPN Menu::vpn_menu"
  "Change WiFi Backend::change_backend"
  "Cancel::exit 0"
)

MENU=$(printf "%s\n" "${OPTIONS[@]%%::*}")

CHOICE=$(fuzzel --dmenu \
  --hide-prompt \
  --lines="${#OPTIONS[@]}" \
  --width="$(wc -L <<<"$MENU")" \
  --config="$HOME/.config/fuzzel/fav-menu.ini" <<<"$MENU")

for entry in "${OPTIONS[@]}"; do
  [[ $CHOICE == "${entry%%::*}" ]] && "${entry##*::}" && break
done
