#!/bin/bash
set -e

if ! systemctl --user is-active --quiet protonmail-bridge.service; then
  systemctl --user start protonmail-bridge.service
  sleep 8
fi
exec betterbird "$@"
exit 1
