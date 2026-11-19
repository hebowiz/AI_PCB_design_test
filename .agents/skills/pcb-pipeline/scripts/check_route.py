"""Fail when Freerouting left connections unrouted.

The router reports zero clearance violations while happily leaving nets
unfinished, and KiCad only discovers it at DRC, after the session has been
imported. Read the router's own summary instead.

  python3 scripts/check_route.py router.log

Set ALLOW_UNROUTED=<n> when a copper pour is expected to finish that many
connections the router could not. Use it only for that: KiCad's DRC is the
real gate, and it is the one that proves the pour actually closed them.
"""

import json
import os
import re
import sys


def summary(text: str) -> dict:
    """The router prints a JSON block last; find the outermost one."""
    start = text.rfind("{")
    while start != -1:
        try:
            return json.loads(text[start:])
        except json.JSONDecodeError:
            start = text.rfind("{", 0, start)
    return {}


def main(log_path: str) -> int:
    text = open(log_path, errors="replace").read()
    stats = summary(text)
    incomplete = stats.get("items", {}).get("incomplete_count")
    violations = stats.get("clearance_violations", {}).get("total_count")

    if incomplete is None:
        passes = re.findall(r"\((\d+) unrouted\)", text)
        incomplete = int(passes[-1]) if passes else None

    allowed = int(os.environ.get("ALLOW_UNROUTED", "0"))
    print(f"unrouted: {incomplete}, clearance violations: {violations}")
    if incomplete and incomplete <= allowed:
        print(f"  {incomplete} left for a copper pour to finish (ALLOW_UNROUTED={allowed})")
        incomplete = 0
    if incomplete:
        print(f"{incomplete} connection(s) left unrouted; raise the pass count",
              file=sys.stderr)
        return 1
    if violations:
        print(f"{violations} clearance violation(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
