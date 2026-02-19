#!/usr/bin/env bash

CIPHER="$HOME/Desktop/Encrypted"
PLAIN="$HOME/Desktop/Decrypted"

initialize_gocrypt() {
  PASSFILE=$(mktemp)
  PASSWORD=$(zenity --password --title="Enter init password")
  echo "$PASSWORD" >"$PASSFILE"
  gocryptfs -init --passfile "$PASSFILE" "$CIPHER"
  shred -u "$PASSFILE"
}

mount_fs() {
  mkdir -p "$CIPHER" "$PLAIN"
  PASSFILE=$(mktemp)
  PASSWORD=$(zenity --password --title="Enter gocryptfs password")
  echo "$PASSWORD" >"$PASSFILE"
  gocryptfs --passfile "$PASSFILE" "$CIPHER" "$PLAIN"
  shred -u "$PASSFILE"
  xdg-open "$PLAIN"
}

main() {
  if [ ! -f "$CIPHER/gocryptfs.conf" ]; then
    initialize_gocrypt
  fi
  if mountpoint -q "$PLAIN"; then
    fusermount3 -u "$PLAIN"
    rmdir "$PLAIN"
  else
    mount_fs
  fi
}
main
