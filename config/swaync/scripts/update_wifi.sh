#!/usr/bin/env bash
set -e

if systemctl is-active --quiet iwd; then
  echo false
else
  echo true
fi
