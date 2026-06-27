#!/bin/bash

CONSERVATION_PATH="/sys/bus/platform/drivers/ideapad_acpi/VPC2004:00/conservation_mode"
if [[ $SWAYNC_TOGGLE_STATE == true ]]; then
  echo 1 | sudo -A tee "$CONSERVATION_PATH" >/dev/null
else
  echo 0 | sudo -A tee "$CONSERVATION_PATH" >/dev/null
fi
