"""Place footprints on a .kicad_pcb by reference designator or atopile address.

  $(scripts/kicad_python.sh) scripts/place.py board.kicad_pcb R1=5,7.5,0 LED1=14,7.5,180
  $(scripts/kicad_python.sh) scripts/place.py board.kicad_pcb board/placement.txt

Positions are mm from the board origin, rotation in degrees. A file argument is
read as one `REF=x,y,rot` per line, `#` starting a comment. Footprints keep their
placement across `ato build`, so this only has to run when the layout changes.
"""

import os

import sys

import pcbnew


def expand(specs: list[str]) -> list[str]:
    """Replace any file argument with the placement lines it holds."""
    out = []
    for spec in specs:
        if os.path.isfile(spec):
            for line in open(spec):
                line = line.split("#", 1)[0].strip()
                if line:
                    out.append(line)
        else:
            out.append(spec)
    return out


def main(pcb_path: str, specs: list[str]) -> int:
    specs = expand(specs)
    board = pcbnew.LoadBoard(pcb_path)
    # 部品番号 (R12) でも atopile の名前 (shunt) でも引ける。部品番号は
    # レイアウトを作り直すと振り直されるので、配置表は名前で書くほうが壊れない
    by_ref = {f.GetReference(): f for f in board.GetFootprints()}
    for f in board.GetFootprints():
        for fld in f.GetFields():
            if fld.GetName() == "atopile_address" and fld.GetText():
                by_ref.setdefault(fld.GetText(), f)
    for spec in specs:
        ref, _, rest = spec.partition("=")
        parts = rest.split(",")
        if ref not in by_ref:
            print(f"no footprint {ref} on board (have {sorted(by_ref)})", file=sys.stderr)
            return 1
        x, y = float(parts[0]), float(parts[1])
        rot = float(parts[2]) if len(parts) > 2 else 0.0
        fp = by_ref[ref]
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        fp.SetOrientationDegrees(rot)
        print(f"{ref} -> {x},{y} @ {rot}deg")
    board.Save(pcb_path)
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2:]))
