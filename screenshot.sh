#!/usr/bin/env bash
set -euo pipefail

WIDTH=800
COLORS=16
MAX_WIDTH=800
CROP_HEIGHT=450  # 16:9 crop, 0 to disable

usage() {
  echo "Usage: $0 <url> [output.jpg] [crop_height|no-crop]"
  exit 1
}

[[ $# -eq 0 ]] && usage

URL="$1"
OUTPUT="${2:-screenshot.jpg}"
STEM="${OUTPUT%.*}"

CROP="${3:-$CROP_HEIGHT}"
[[ "$CROP" == "no-crop" ]] && CROP=0

TMP=$(mktemp ./screenshot_XXXXXX.png)

chromium --headless --screenshot="$TMP" --window-size="${WIDTH},2000" "$URL" 2>/dev/null

CROP_ARG=()
[[ "$CROP" -gt 0 ]] && CROP_ARG=(-gravity North -crop "${WIDTH}x${CROP}+0+0" +repage)

convert "$TMP" \
  "${CROP_ARG[@]}" \
  -thumbnail "${MAX_WIDTH}x>" \
  -posterize 8 \
  -dither Riemersma \
  -colors "$COLORS" \
  -quality 75 \
  "${STEM}.jpg"

rm "$TMP"
echo "$URL -> ${STEM}.jpg"
