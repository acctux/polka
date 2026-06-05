#!/usr/bin/env bash
set -euo pipefail

mkdir -p "${XDG_CONFIG_HOME}/neomutt"
khard export neomutt >"${XDG_CONFIG_HOME}/neomutt/alias"
