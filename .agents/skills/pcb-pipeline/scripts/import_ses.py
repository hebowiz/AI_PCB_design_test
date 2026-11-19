"""Read a Freerouting .ses session file back into a .kicad_pcb.

Run with KiCad's bundled python:  $(scripts/kicad_python.sh) scripts/import_ses.py board.kicad_pcb routed.ses
The board is saved in place; keep it under version control so the import is reversible.
"""

import sys

import pcbnew


def main(pcb_path: str, ses_path: str) -> int:
    board = pcbnew.LoadBoard(pcb_path)
    if not pcbnew.ImportSpecctraSES(board, ses_path):
        print(f"ImportSpecctraSES failed for {ses_path}", file=sys.stderr)
        return 1
    board.Save(pcb_path)
    tracks = len(board.GetTracks())
    print(f"imported {ses_path} into {pcb_path} ({tracks} track/via objects)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
