#!/usr/bin/env bash
set -euo pipefail

PREFIX="web_"
MAX_WIDTH=500
COLORS=16
DETOUR=0

usage() {
  echo "Usage: $0 [--detour] <image> [image ...]"
  exit 1
}

[[ $# -eq 0 ]] && usage

# parse flags
ARGS=()
for ARG in "$@"; do
  if [[ "$ARG" == "--detour" ]]; then
    DETOUR=1
  else
    ARGS+=("$ARG")
  fi
done

[[ ${#ARGS[@]} -eq 0 ]] && usage

for INPUT in "${ARGS[@]}"; do
  [[ ! -f "$INPUT" ]] && { echo "Not found: $INPUT"; continue; }

  DIR=$(dirname "$INPUT")
  FILENAME=$(basename "$INPUT")
  STEM="${FILENAME%.*}"
  # slugify: lowercase, collapse non-alnum runs to hyphens, trim edge hyphens
  SLUG=$(echo "$STEM" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g; s/^-//; s/-$//')

  # --detour forces PNG (needs alpha); otherwise PNG only if source has alpha
  if [[ "$DETOUR" -eq 1 ]]; then
    EXT="png"
  elif convert "$INPUT" -format "%[channels]" info: 2>/dev/null | grep -q "a"; then
    EXT="png"
  else
    EXT="jpg"
  fi
  OUTPUT="$DIR/${PREFIX}${SLUG}.${EXT}"

  if [[ "$DETOUR" -eq 1 ]]; then
    convert "$INPUT" \
      -thumbnail "${MAX_WIDTH}x>" \
      -fuzz 10% -transparent white \
      -posterize 8 \
      -dither Riemersma \
      -colors "$COLORS" \
      "$OUTPUT"
  else
    convert "$INPUT" \
      -thumbnail "${MAX_WIDTH}x>" \
      -posterize 8 \
      -dither Riemersma \
      -colors "$COLORS" \
      -quality 75 \
      "$OUTPUT"
  fi

  echo "$INPUT -> $OUTPUT"
done
