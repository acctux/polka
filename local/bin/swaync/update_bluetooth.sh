#!/usr/bin/env bash
set -e

if systemctl is-active --quiet bluetooth; then
  echo false
else
  echo true
fi
