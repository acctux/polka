#!/usr/bin/env bash
quotes_file="$HOME/.local/bin/wall/quotes.yaml"

python3 - "$quotes_file" <<'PY'
import random
import sys
import yaml

with open(sys.argv[1], encoding="utf-8") as f:
    quotes = yaml.safe_load(f) or []

eligible = [q for q in quotes if not q.get("controversial", False)]
if not eligible:
    sys.exit("No non-controversial quotes found.")

quote = random.choice(eligible)
print(f'"{quote["text"]}" — {quote["author"]}')
PY
