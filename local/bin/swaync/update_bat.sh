#!/usr/bin/env bash
set -e

# Path to the conservation mode file
CONSERVATION_PATH="/sys/bus/platform/drivers/ideapad_acpi/VPC2004:00/conservation_mode"

# Output true if mode is 1 (ON), false if 0 (OFF)
if [[ $(cat "$CONSERVATION_PATH") == "1" ]]; then
  echo true
else
  echo false
fi
