#!/usr/bin/env bash
set +e # disable immediate exit on error

if [[ $SWAYNC_TOGGLE_STATE == true ]]; then
  bluetoothctl power off
else
  bluetoothctl power on
fi

exit 0
