#!/bin/bash
set -e

if ! systemctl --user is-active --quiet protonmail-bridge.service; then
  systemctl --user start protonmail-bridge.service
  sleep 12
fi
"$HOME/.local/bin/email/emailsync.sh"
exec kitty neomutt
exit 1
