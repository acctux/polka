#!/usr/bin/env bash

# Path to your Python script
PY_SCRIPT="$HOME/Polka/local/bin/unarchive/unarchive.py"

# Ensure at least one file is selected
if [ -z "$NEMO_SCRIPT_SELECTED_FILE_PATHS" ]; then
  echo "No files selected."
  exit 1
fi

# Launch Alacritty and pass all selected files to the Python script
# Convert newlines to spaces for proper argument passing
alacritty -e python "$PY_SCRIPT" $(echo "$NEMO_SCRIPT_SELECTED_FILE_PATHS" | tr '\n' ' ')
