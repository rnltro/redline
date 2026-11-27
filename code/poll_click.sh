#!/bin/bash
# Poll for an element by text and click it when found (hydration-safe).
# usage: poll_click.sh "button text" [max_tries]
TEXT="$1"
TRIES="${2:-20}"
for i in $(seq 1 "$TRIES"); do
  if agent-browser find text "$TEXT" click 2>/dev/null; then
    echo "CLICKED: $TEXT (try $i)"
    exit 0
  fi
  sleep 0.7
done
echo "FAILED to find: $TEXT"
exit 1
