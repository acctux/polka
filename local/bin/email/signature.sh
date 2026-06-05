#!/usr/bin/env bash
# Prints one random line from the quotes file
quotes_file="$HOME/.local/bin/wall/quotes.txt"
shuf -n 1 "$quotes_file"
