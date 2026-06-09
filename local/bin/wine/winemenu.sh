#!/usr/bin/env bash

# -----------------------------
# Config
# -----------------------------
CONFIG="$HOME/.config/fuzzel/waybar.ini"
# -----------------------------
# Menu items
# -----------------------------
declare -A MENU_MAP=(
  ["Create Wine Prefix"]="python \"$HOME/Lit/polka/local/bin/wine/prefix.py\""
  ["Run Wine Exe"]="python \"$HOME/Lit/polka/local/bin/wine/runwine.py\""
  ["Cancel"]="exit 0"
)
MENU_ORDER=(
  "Create Wine Prefix"
  "Run Wine Exe"
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
