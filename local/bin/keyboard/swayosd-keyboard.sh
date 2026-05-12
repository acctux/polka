#!/bin/bash

device=$(basename /sys/class/leds/*kbd_backlight* 2>/dev/null)
[[ -z "$device" ]] && exit 1

max=2
current=$(brightnessctl -d "$device" get)
new=$(((current + 1) % (max + 1)))
brightnessctl -d "$device" set "$new" >/dev/null
percent=$((new * 100 / max))
progress=$(awk "BEGIN { printf \"%.2f\", $percent/100 }")
[[ "$progress" == "0.00" ]] && progress="0.01"
monitor=$(hyprctl monitors -j | jq -r '.[] | select(.focused).name')
swayosd-client \
  --monitor "$monitor" \
  --custom-icon keyboard-brightness-symbolic \
  --custom-progress "$progress" \
  --custom-progress-text "${percent}%"
