#!/usr/bin/env bash
set -euo pipefail

LOCKDIR="${XDG_RUNTIME_DIR:-/tmp}/emailsync.lock"

fetch_mail() {
  echo "Fetching email..."
  mbsync -a
  echo "Email fetched."
}
index_mail() {
  echo "Updating notmuch database..."
  notmuch new
  echo "Notmuch indexing complete."
}
acquire_lock() {
  if ! mkdir "$LOCKDIR" 2>/dev/null; then
    echo "Another email sync is already running. Exiting."
    exit 1
  fi
  # Ensure lock removal on exit
  trap 'rm -rf "$LOCKDIR"' EXIT
}
main() {
  echo "Starting email synchronization..."
  acquire_lock
  fetch_mail
  index_mail
  echo "Email synchronization complete."
}
main "$@"
