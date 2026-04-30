#!/bin/bash

ICON=""
ANDROID_MOUNT="/run/media/$(whoami)/Phone/Internal" # Dynamic path based on the username
DISCONNECTED="{\"text\": \"\"}"
CONNECTED="{\"text\": \"$ICON\", \"tooltip\": \"Phone connected\t\n\nLeft: Mount Phone\t\nMiddle: KDE Connect\t\nRight: SMS\", \"class\": \"connected\"}"
MOUNTED="{\"text\": \"$ICON\", \"tooltip\": \"Phone mounted\", \"class\": \"mounted\"}"
STATE="$DISCONNECTED"

is_phone_mounted() {
  if [ ! -d "$ANDROID_MOUNT" ]; then
    return 1
  fi
  if [ -z "$(find "$ANDROID_MOUNT" -maxdepth 1 -type d)" ]; then
    return 1
  fi
  return 0
}

is_reachable() {
  if kdeconnect-cli -l | grep -iq "paired and reachable"; then
    return 0
  else
    return 1
  fi
}

if is_reachable; then
  STATE="$CONNECTED"
  if is_phone_mounted; then
    STATE="$MOUNTED"
  fi
fi

echo "$STATE"
