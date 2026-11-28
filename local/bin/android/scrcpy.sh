#!/usr/bin/env bash

opts=(-m 1280 --video-codec=h265 --turn-screen-off
  --stay-awake --power-off-on-close)

scrcpy --tcpip "${opts[@]}" ||
  scrcpy --tcpip=192.168.12.176 "${opts[@]}" ||
  scrcpy -d "${opts[@]}"
