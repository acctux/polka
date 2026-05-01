#!/bin/bash

if pgrep -x "NetworkManager" >/dev/null; then
  kitty nmtui
elif pgrep -x "iwd" >/dev/null; then
  kitty impala
else
  exit 1
fi
