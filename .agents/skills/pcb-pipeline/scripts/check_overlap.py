"""List footprint pairs whose outlines overlap.

EasyEDA footprints made by `ato create part` carry no courtyard, so KiCad's
courtyard DRC finds nothing. This compares footprint bounding boxes (pads,
silkscreen and fab graphics, no text). Small overlaps are usually two silk
outlines touching; anything over ~0.5 mm in both directions deserves a look at
the real body sizes (a TVS under a terminal block, a capacitor under an
electrolytic's base plate).

  $(scripts/kicad_python.sh) scripts/check_overlap.py board.kicad_pcb [min_mm]
"""

import os
import sys

import pcbnew


def main(path: str, min_mm: float) -> int:
    board = pcbnew.LoadBoard(path)
    boxes = []
    for fp in board.GetFootprints():
        bb = fp.GetBoundingBox(False, False)
        boxes.append((fp.GetReference(), pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                      pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())))
    hits = 0
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ox = min(a[3], b[3]) - max(a[1], b[1])
            oy = min(a[4], b[4]) - max(a[2], b[2])
            if ox > min_mm and oy > min_mm:
                print(f"{a[0]:6s} {b[0]:6s} overlap {ox:.2f} x {oy:.2f} mm")
                hits += 1
    print(f"{hits} overlapping pair(s) over {min_mm} mm")
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    code = main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) == 3 else 0.5)
    sys.stdout.flush()
    os._exit(code)
