"""Turn the build output into the BOM and placement (CPL) files a fab's assembly order wants.

  python3 scripts/fab_files.py <fab> out/default.pos.csv board/build/builds/default/default.bom.csv out/<fab> \
      [board.kicad_pcb j_in,j_out,...]

<fab> picks a profile from FABS below: column names, which BOM column holds the
part number the fab orders by, how sides are spelled. Only profiles that were
checked against a real order belong here. For a fab that is not listed, look up
its current BOM / CPL format first and add a profile (references/fab/README.md).

The placement file comes from `kicad-cli pcb export pos`, so it shares the
gerbers' coordinate frame; this only renames columns. Footprints excluded from
position files (mounting holes, bare-copper features) never appear in either file.

Parts to be hand-soldered are named by their atopile instance name (designators
are renumbered whenever the layout is rebuilt), looked up in the board file, and
left out of both files. Plain designators work too, for boards without atopile.
"""

import csv
import os
import re
import sys

FABS = {
    # references/fab/jlcpcb.md。2026-09 の発注で通った形
    "jlcpcb": dict(
        bom=("Comment", "Designator", "Footprint", "LCSC Part #"),
        part="LCSC Part #",           # 発注に使う型番の列 (atopile の BOM の列名)
        cpl=("Designator", "Mid X", "Mid Y", "Layer", "Rotation"),
        sides=("top", "bottom"),
        ascii=True,                   # BOM 画面が UTF-8 の Ω, ±, µ を化けさせる
    ),
    # 業者を決める前の確認用。メーカー型番で引く汎用の形。そのまま発注には使わない
    "generic": dict(
        bom=("Comment", "Designator", "Footprint", "Manufacturer", "Partnumber"),
        part="Partnumber",
        cpl=("Designator", "Mid X", "Mid Y", "Layer", "Rotation"),
        sides=("top", "bottom"),
        ascii=False,
    ),
}


def designators_of(pcb_path: str, names: list) -> dict:
    """atopile のインスタンス名 (または部品番号) -> 部品番号。基板ファイルから引く。"""
    found = {}
    for block in open(pcb_path).read().split("\n\t(footprint ")[1:]:
        ref = re.search(r'\(property "Reference" "([^"]+)"', block)
        addr = re.search(r'\(property "atopile_address" "([^"]+)"', block)
        if ref and addr and addr.group(1) in names:
            found[addr.group(1)] = ref.group(1)
        elif ref and ref.group(1) in names:
            found[ref.group(1)] = ref.group(1)
    missing = [a for a in names if a not in found]
    if missing:
        raise SystemExit(f"not on the board: {', '.join(missing)}")
    return found


def write_bom(fab: dict, bom_path: str, out_dir: str, skip: set) -> list:
    rows = []
    for row in csv.DictReader(open(bom_path)):
        if not (row.get(fab["part"]) or "").strip():
            continue
        designators = [d.strip() for d in row["Designator"].split(",") if d.strip() and d.strip() not in skip]
        if not designators:
            continue
        value = (row.get("Value") or "").strip() or (row.get("Partnumber") or "").strip()
        # atopile writes solver artefacts such as "ℝ+V" into the value column
        value = re.sub(r"\s*ℝ\+[A-Z]", "", value).strip()
        if fab["ascii"]:
            for a, b in (("Ω", "R"), ("±", "+/-"), ("µ", "u"), ("μ", "u")):
                value = value.replace(a, b)
        src = dict(row, Comment=value, Designator=",".join(designators),
                   Footprint=(row.get("Footprint") or "").split(":")[-1])
        rows.append({c: (src.get(c) or "").strip() for c in fab["bom"]})
    with open(os.path.join(out_dir, "bom.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fab["bom"])
        w.writeheader()
        w.writerows(rows)
    return rows


def write_cpl(fab: dict, pos_path: str, out_dir: str, skip: set) -> list:
    rows = []
    d, x, y, side, rot = fab["cpl"]
    for row in csv.DictReader(open(pos_path)):
        if row["Ref"] in skip:
            continue
        top = row["Side"].lower() in ("top", "front")
        rows.append({d: row["Ref"], x: row["PosX"], y: row["PosY"],
                     side: fab["sides"][0 if top else 1], rot: row["Rot"]})
    with open(os.path.join(out_dir, "cpl.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fab["cpl"])
        w.writeheader()
        w.writerows(rows)
    return rows


def main(fab_name: str, pos_path: str, bom_path: str, out_dir: str, pcb_path: str = "", hand: str = "") -> int:
    if fab_name not in FABS:
        print(f"no profile for {fab_name} (have {', '.join(FABS)}); add one to FABS", file=sys.stderr)
        return 2
    fab = FABS[fab_name]
    os.makedirs(out_dir, exist_ok=True)
    skip = designators_of(pcb_path, [a for a in hand.split(",") if a]) if hand else {}
    bom = write_bom(fab, bom_path, out_dir, set(skip.values()))
    cpl = write_cpl(fab, pos_path, out_dir, set(skip.values()))

    in_bom = {d for r in bom for d in r["Designator"].split(",")}
    placed = {r[fab["cpl"][0]] for r in cpl}
    print(f"{out_dir}/bom.csv: {len(bom)} line(s), {len(in_bom)} part(s)")
    print(f"{out_dir}/cpl.csv: {len(cpl)} placement(s)")
    if skip:
        print("  hand-soldered, left out: " + ", ".join(f"{r} ({a})" for a, r in sorted(skip.items())))
    missing = sorted(in_bom - placed)
    extra = sorted(placed - in_bom)
    if missing:
        print(f"  in the BOM but not placed: {', '.join(missing)}")
    if extra:
        print(f"  placed but not in the BOM (no {fab['part']}?): {', '.join(extra)}")
    return 1 if (missing or extra) else 0


if __name__ == "__main__":
    if len(sys.argv) not in (5, 7):
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(*sys.argv[1:]))
