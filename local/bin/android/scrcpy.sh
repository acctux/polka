#!/bin/bash

scrcpy --tcpip \
  -e \
  -m1280 \
  --video-codec=h265 \
  --turn-screen-off \
  --stay-awake \
  --power-off-on-close ||
  scrcpy --tcpip=192.168.12.176 \
    -m1280 \
    --video-codec=h265 \
    --turn-screen-off \
    --stay-awake \
    --power-off-on-close ||
  scrcpy -d \
    -m1280 \
    --video-codec=h265 \
    --turn-screen-off \
    --stay-awake \
    --power-off-on-close
