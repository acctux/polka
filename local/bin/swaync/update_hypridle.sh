#!/usr/bin/env bash
set -e

if systemctl --user is-active --quiet hypridle; then
  echo false
else
  echo true
fi
