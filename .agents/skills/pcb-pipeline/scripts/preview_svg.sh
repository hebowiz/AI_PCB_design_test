#!/usr/bin/env bash
# Rasterise an SVG for eyeballing.
# rsvg-convert (librsvg) when it is installed; otherwise macOS' Quick Look, which
# renders into a square and crops, so the canvas is padded to a square first.
set -euo pipefail
SRC="$1"
OUT_DIR="${2:-$(dirname "$SRC")}"
PNG="$OUT_DIR/$(basename "${SRC%.svg}").png"
if command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert -w 2000 -b white "$SRC" -o "$PNG"
  echo "$PNG"
  exit 0
fi
command -v qlmanage >/dev/null 2>&1 || { echo "need rsvg-convert (librsvg) or macOS qlmanage" >&2; exit 1; }
SIDE=$(python3 - "$SRC" <<'PY'
import re, sys
head = open(sys.argv[1]).read(400)
w = int(float(re.search(r'width="([\d.]+)"', head).group(1)))
h = int(float(re.search(r'height="([\d.]+)"', head).group(1)))
print(max(w, h))
PY
)
TMP="$(mktemp -d)/square.svg"
python3 - "$SRC" "$TMP" "$SIDE" <<'PY'
import re, sys
src, dst, side = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(src).read()
s = re.sub(r'width="[\d.]+" height="[\d.]+"', f'width="{side}" height="{side}"', s, count=1)
s = re.sub(r'viewBox="[^"]+"', f'viewBox="0 0 {side} {side}"', s, count=1)
open(dst, "w").write(s)
PY
qlmanage -t -s 2000 -o "$OUT_DIR" "$TMP" >/dev/null 2>&1
mv "$OUT_DIR/square.svg.png" "$PNG"
echo "$PNG"
