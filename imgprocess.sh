#!/usr/bin/env bash
set -euo pipefail

PREFIX="web_"
MAX_WIDTH=500
COLORS=16

usage() {
  echo "Usage: $0 <image> [image ...]"
  exit 1
}

[[ $# -eq 0 ]] && usage

for INPUT in "$@"; do
  [[ ! -f "$INPUT" ]] && { echo "Not found: $INPUT"; continue; }

  DIR=$(dirname "$INPUT")
  FILENAME=$(basename "$INPUT")

  # use PNG to preserve alpha, otherwise JPEG
  if convert "$INPUT" -format "%[channels]" info: 2>/dev/null | grep -q "a"; then
    EXT="png"
  else
    EXT="jpg"
  fi
  OUTPUT="$DIR/${PREFIX}${FILENAME%.*}.${EXT}"

  convert "$INPUT" \
    -resize "${MAX_WIDTH}x>" \
    -posterize 8 \
    -dither Riemersma \
    -colors "$COLORS" \
    -quality 75 \
    "$OUTPUT"

  echo "$INPUT -> $OUTPUT"
done
