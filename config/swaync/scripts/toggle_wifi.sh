#!/usr/bin/env bash
set +e

# Toggle iwd.service
if systemctl is-active --quiet iwd.service; then
  echo "Stopping iwd.service (Wi-Fi OFF)"
  sudo -A systemctl stop iwd.service
else
  echo "Starting iwd.service (Wi-Fi ON)"
  sudo -A systemctl start iwd.service
fi

exit 0
