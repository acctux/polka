#!/bin/bash
set -e

if ! systemctl --user is-active --quiet deluged.service; then
  systemctl --user start deluged.service
  sleep 2
fi

for _ in {1..30}; do
  if deluge-console info >/dev/null 2>&1; then
    exec deluge-gtk "$@"
  fi
done

exit 1
