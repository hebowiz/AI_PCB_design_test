"""Print the layers a fab needs, for `kicad-cli pcb export gerbers --layers`.

Copper layers are read from the board, so the list follows the layer count
(2, 4, 6 ... layers) without editing the Makefile. Fab, Courtyard and User
layers are left out: in an order zip they can be mistaken for the board outline.

  python3 scripts/gerber_layers.py board.kicad_pcb
"""

import re
import sys

FIXED = ["F.Paste", "B.Paste", "F.Silkscreen", "B.Silkscreen", "F.Mask", "B.Mask", "Edge.Cuts"]


def copper(pcb_path: str) -> list:
    text = open(pcb_path).read()
    table = re.search(r"\n\t\(layers\n(.*?)\n\t\)", text, re.S)
    if not table:
        raise SystemExit(f"no layer table in {pcb_path}")
    names = re.findall(r'\(\d+ "([^"]+\.Cu)" (?:signal|power|mixed|jumper)', table.group(1))
    # 表、内層 (番号順)、裏
    inner = sorted((n for n in names if n.startswith("In")), key=lambda n: int(n[2:-3]))
    return ["F.Cu"] + inner + ["B.Cu"]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    print(",".join(copper(sys.argv[1]) + FIXED))
