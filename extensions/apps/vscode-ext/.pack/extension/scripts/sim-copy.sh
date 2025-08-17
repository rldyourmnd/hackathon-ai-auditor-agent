#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-}"

case "$ACTION" in
  copy)
    xdotool key ctrl+a || true
    sleep 0.05
    xdotool key ctrl+c
    sleep 0.06
    ;;
  paste)
    xdotool key ctrl+v
    sleep 0.06
    ;;
  send)
    xdotool key Return
    sleep 0.04
    ;;
  pasteAndSend)
    xdotool key ctrl+v
    sleep 0.04
    xdotool key Return
    sleep 0.04
    ;;
  *)
    echo "Unknown action: $ACTION" >&2
    exit 2
    ;;
esac


