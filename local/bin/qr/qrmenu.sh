#!/usr/bin/env bash

# -----------------------------
# Config
# -----------------------------
CONFIG="$HOME/.config/fuzzel/waybar.ini"
# -----------------------------
# Menu items
# -----------------------------
declare -A MENU_MAP=(
  ["Show WiFi QR"]="kitty --hold $HOME/.local/bin/qr/wifiqr.py"
  ["Scan QR From Screenshot"]="$HOME/.local/bin/qr/qr.py"
  ["Scan QR From Webcam"]="zbarcam-gtk"
  ["Cancel"]="exit 0"
)
MENU_ORDER=(
  "Show WiFi QR"
  "Scan QR From Screenshot"
  "Scan QR From Webcam"
  "Cancel"
)
# -----------------------------
# Build menu
# -----------------------------
MENU=$(printf "%s\n" "${MENU_ORDER[@]}")
LINES=$(wc -l <<<"$MENU")
WIDTH=$(wc -L <<<"$MENU")
CHOICE=$(fuzzel --dmenu \
  --hide-prompt \
  --lines="$LINES" \
  --width="$WIDTH" \
  --config="$CONFIG" <<<"$MENU")
# -----------------------------
# Execute
# -----------------------------
[[ -z "$CHOICE" ]] && exit 0
ACTION="${MENU_MAP[$CHOICE]}"
[[ -z "$ACTION" ]] && exit 0
[[ "$ACTION" == "exit 0" ]] && exit 0
eval "$ACTION"
