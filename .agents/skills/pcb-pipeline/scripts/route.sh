#!/usr/bin/env bash
# Autoroute a Specctra DSN with Freerouting, headless, and write a SES session file.
#   scripts/route.sh in.dsn out.ses [max_passes]
# Freerouting only goes headless via a freerouting.json next to the working directory,
# so we run it inside a scratch dir that holds that config.
set -euo pipefail

DSN="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
SES_DIR="$(cd "$(dirname "$2")" && pwd)"
SES="$SES_DIR/$(basename "$2")"
PASSES="${3:-20}"
JAR="${FREEROUTING_JAR:-$HOME/tools/freerouting-2.1.0.jar}"

[ -f "$JAR" ] || { echo "Freerouting jar not found: $JAR (set FREEROUTING_JAR)" >&2; exit 1; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
# -mp だけでは 2.1.0 はパス数を止めない。router.max_passes と job_timeout で縛る
cat > "$WORK/freerouting.json" <<JSON
{
  "gui": { "enabled": false },
  "feature_flags": { "logging": true },
  "profile": { "email": "", "id": "" },
  "router": {
    "max_passes": $PASSES,
    "job_timeout": "${ROUTE_TIMEOUT:-00:08:00}",
    "optimizer": { "enabled": ${ROUTE_OPTIMIZE:-false} }
  }
}
JSON

HERE="$(cd "$(dirname "$0")" && pwd)"
( cd "$WORK" && java -Djava.awt.headless=true -jar "$JAR" \
    -de "$DSN" -do "$SES" -mp "$PASSES" ) > "$SES_DIR/router.log" 2>&1 || true
cp "$SES_DIR/router.log" "$WORK/router.log"

[ -s "$SES" ] || { echo "Freerouting produced no session file" >&2; exit 1; }
python3 "$HERE/check_route.py" "$WORK/router.log"
echo "wrote $SES"
