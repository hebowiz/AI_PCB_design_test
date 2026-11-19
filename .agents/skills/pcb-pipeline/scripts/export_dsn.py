"""Export a .kicad_pcb to a Specctra .dsn file for Freerouting.

Run with KiCad's bundled python:  $(scripts/kicad_python.sh) scripts/export_dsn.py board.kicad_pcb out.dsn
kicad-cli has no DSN exporter, so we drive pcbnew directly.
"""

import sys

import pcbnew


def main(pcb_path: str, dsn_path: str) -> int:
    board = pcbnew.LoadBoard(pcb_path)
    if not pcbnew.ExportSpecctraDSN(board, dsn_path):
        print(f"ExportSpecctraDSN failed for {pcb_path}", file=sys.stderr)
        return 1
    print(f"wrote {dsn_path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
