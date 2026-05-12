#!/bin/bash
wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle >/dev/null
if pactl get-source-mute @DEFAULT_SOURCE@ | rg -q 'yes'; then
  led=on
  osd_message='Mic muted'
  osd_icon='microphone-sensitivity-muted-symbolic'
else
  led=off
  osd_message='Mic on'
  osd_icon='audio-input-microphone-symbolic'
fi
swayosd-client \
  --custom-message "$osd_message" \
  --custom-icon "$osd_icon"
