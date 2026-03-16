#!/bin/bash

scrcpy --tcpip \
  -e \
  -m1280 \
  --video-codec=h265 \
  --turn-screen-off \
  --stay-awake \
  --power-off-on-close
