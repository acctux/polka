#!/usr/bin/env bash

FILE="/var/cache/mysysinfo/sysinfo.txt"
if [[ ! -f "$FILE" ]]; then
  echo '{"text":"󰌢","tooltip":"sysinfo unavailable"}'
  exit 0
fi
family=$(grep -m1 "^Manufacturer:" "$FILE" | cut -d':' -f2- | xargs)
tooltip=$(awk '{printf "%s\\n", $0}' "$FILE")
printf '{"text":"󰌢 %s","tooltip":"%s"}\n' "$family" "$tooltip\t"
