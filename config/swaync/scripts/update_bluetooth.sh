#!/usr/bin/env bash
set -e

powered=$(bt-adapter -i | awk -F': ' '/Powered:/ {print $2}' | awk '{print $1}')

if [ "$powered" = "1" ]; then
  echo false
else
  echo true
fi
