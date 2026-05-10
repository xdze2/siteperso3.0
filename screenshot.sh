#!/usr/bin/env bash
set -euo pipefail

WIDTH=800
COLORS=16
MAX_WIDTH=800

usage() {
  echo "Usage: $0 <url> [output.jpg]"
  exit 1
}

[[ $# -eq 0 ]] && usage

URL="$1"
OUTPUT="${2:-screenshot.jpg}"
STEM="${OUTPUT%.*}"
TMP=$(mktemp /tmp/screenshot_XXXXXX.png)

chromium --headless --screenshot="$TMP" --window-size="${WIDTH},2000" "$URL" 2>/dev/null

convert "$TMP" \
  -thumbnail "${MAX_WIDTH}x>" \
  -posterize 8 \
  -dither Riemersma \
  -colors "$COLORS" \
  -quality 75 \
  "${STEM}.jpg"

rm "$TMP"
echo "$URL -> ${STEM}.jpg"
