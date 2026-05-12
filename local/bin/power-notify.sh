#!/usr/bin/env bash

USER_NAME="$(loginctl list-sessions --no-legend | awk '$3 != "" {print $3; exit}')"
USER_ID="$(id -u "$USER_NAME")"

export XDG_RUNTIME_DIR="/run/user/$USER_ID"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"

sudo -u "$USER_NAME" \
  env XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
  DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" \
  /usr/bin/notify-send "Power" "$1"
