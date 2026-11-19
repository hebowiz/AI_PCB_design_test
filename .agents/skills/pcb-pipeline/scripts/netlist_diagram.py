"""Draw the circuit from the board, since atopile emits no schematic.

atopile 0.15.8 produces a .kicad_pcb and reports, never a .kicad_sch, so there
is nothing for KiCad's schematic editor to open. This renders the same
information as a connection graph: every component, every net that joins two
or more pins, and which pin sits on which net.

Output is Markdown with a mermaid diagram, which GitHub and VS Code preview
without anything installed.

  $(scripts/kicad_python.sh) scripts/netlist_diagram.py board.kicad_pcb out/netlist.md [bom.csv]

The BOM is optional and only supplies each designator's value; without it the
diagram still shows every part and net, just unlabelled.
"""

import csv
import os
import sys
from collections import defaultdict

import pcbnew

POWER_HINTS = ("lv", "gnd", "hv", "vbat", "vcc", "vdd")


def values_from_bom(bom: str) -> dict:
    """Pick up each designator's value so the diagram reads like a schematic."""
    out = {}
    if not bom or not os.path.exists(bom):
        return out
    for row in csv.DictReader(open(bom)):
        value = (row.get("Value") or "").strip() or (row.get("Partnumber") or "").strip()
        for ref in (row.get("Designator") or "").split(","):
            ref = ref.strip()
            if ref:
                out[ref] = value
    return out


def main(pcb_path: str, md_path: str, bom_path: str = "") -> int:
    board = pcbnew.LoadBoard(pcb_path)
    values = values_from_bom(bom_path)

    nets = defaultdict(list)
    for pad in board.GetPads():
        name = pad.GetNetname()
        if name:
            ref = pad.GetParentFootprint().GetReference()
            nets[name].append((ref, pad.GetNumber()))

    shared = {n: sorted(set(p)) for n, p in nets.items() if len(set(p)) > 1}
    refs = sorted({r for pins in shared.values() for r, _ in pins})

    lines = [
        "# 回路の接続",
        "",
        "atopile は回路図ファイルを出力しない。これは基板のネットから起こした接続図。",
        "",
        "```mermaid",
        "graph LR",
    ]
    for ref in refs:
        label = f"{ref}<br/>{values[ref]}" if values.get(ref) else ref
        lines.append(f'  {ref}["{label}"]')
    for net in sorted(shared):
        shape = "((%s))" if net.lower() in POWER_HINTS else "{{%s}}"
        lines.append(f"  NET_{net}{shape % net}")
    for net, pins in sorted(shared.items()):
        for ref, pin in pins:
            lines.append(f"  {ref} ---|{pin}| NET_{net}")
    lines += ["```", "", "## ネット一覧", "", "| ネット | 接続先 |", "| --- | --- |"]
    for net, pins in sorted(shared.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        joined = ", ".join(f"{r}.{p}" for r, p in pins)
        lines.append(f"| {net} | {joined} |")

    single = sorted(n for n, p in nets.items() if len(set(p)) == 1)
    if single:
        # 1 ピンしか載っていないネット。意図した開放か、配線漏れかを目で確かめる
        lines += ["", f"1 ピンだけのネットが {len(single)} 本ある。意図した開放か確かめること。", ""]
        for n in single:
            lines.append(f"- {n}: " + ", ".join(sorted({f'{r}.{p}' for r, p in nets[n]})))

    os.makedirs(os.path.dirname(md_path) or ".", exist_ok=True)
    open(md_path, "w").write("\n".join(lines) + "\n")
    print(f"wrote {md_path}: {len(refs)} parts, {len(shared)} nets")
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(*sys.argv[1:]))
