#!/usr/bin/env bash
# Print the Python interpreter that can `import pcbnew`.
#   macOS:   the one bundled in KiCad.app (KICAD_APP to point elsewhere)
#   Linux:   the system python3 the KiCad package installs pcbnew into
#   KICAD_PYTHON overrides both.
set -euo pipefail
if [ -n "${KICAD_PYTHON:-}" ]; then echo "$KICAD_PYTHON"; exit 0; fi
KICAD_APP="${KICAD_APP:-/Applications/KiCad/KiCad.app}"
for p in "$KICAD_APP"/Contents/Frameworks/Python.framework/Versions/*/bin/python3; do
  [ -x "$p" ] && echo "$p" && exit 0
done
for p in /usr/bin/python3 python3; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c "import pcbnew" >/dev/null 2>&1; then
    command -v "$p"; exit 0
  fi
done
echo "no python with pcbnew found (looked in $KICAD_APP and python3); set KICAD_PYTHON" >&2
exit 1
