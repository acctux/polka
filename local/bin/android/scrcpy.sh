#!/bin/bash

IP_ADDRESS="192.168.12.176"
scrcpy --tcpip="$IP_ADDRESS" \
  -m960 \
  --video-codec=h265 \
  --turn-screen-off \
  --stay-awake \
  --power-off-on-close
