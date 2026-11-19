"""Rip up routing before re-routing, keeping anything locked.

Tracks from a previous run survive a re-placement and go into the next DSN as
existing wiring. The router then has to work around copper that no longer
matches the layout, and quietly leaves connections unrouted. Clear them first.

Locked tracks are kept: that is how hand-routed critical nets are protected.

Pours added after routing (zones named auto-pcb-post-*) are cleared too. They are
re-added after the session comes back, and leaving them in place would send them
to the router as planes, which on a two-layer board leaves it nowhere to put the
signals. Copper and keep-outs placed before routing (auto-pcb-pre-*, -keep-*,
-route-*) are kept, because the router does need to see those.

  $(scripts/kicad_python.sh) scripts/unroute.py board.kicad_pcb
"""

import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbkit import POST  # noqa: E402


def main(pcb_path: str) -> int:
    board = pcbnew.LoadBoard(pcb_path)
    tracks = [t for t in board.GetTracks() if not t.IsLocked()]
    locked = len(board.GetTracks()) - len(tracks)
    zones = [z for z in board.Zones() if (z.GetZoneName() or "").startswith(POST)]
    for item in tracks + zones:
        board.Remove(item)
    board.Save(pcb_path)
    print(
        f"ripped up {len(tracks)} track/via object(s) and {len(zones)} pour(s), "
        f"kept {locked} locked track(s)"
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    code = main(sys.argv[1])
    sys.stdout.flush()
    os._exit(code)
