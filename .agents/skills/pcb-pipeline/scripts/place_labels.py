"""シルクの部品番号を、部品に隠れず読める位置に置き直す。

atopile のフットプリントは部品番号を外形のすぐ上か下に置く。部品が詰まった
基板ではそこが隣の部品の本体やパッドの上になり、実装後に読めなくなる。

  * 部品番号は JLCPCB の下限 (高さ 1.0mm, 線幅 0.15mm) に揃え、値は出さない
  * 自分と他の部品の本体 (パッドと外形線の範囲)、パッド、基板の縁、置いた部品番号を
    避けて、本体の上下左右を 0 度と 90 度で滑らせながら一番近い空きを探す
  * 置き場の少ない部品から先に決める。どこにも置けないものは F.Fab に移して一覧に出す
  * 外形線が 0.15mm より細いシルクは 0.15mm に太らせる (JLCPCB の下限)

EasyEDA 由来のフットプリントにはコートヤードが無いので、本体の範囲はパッドと
シルク・Fab の外形線の外接矩形で見積もる。配線やベタには触らない。何度流してもよい。

  $(scripts/kicad_python.sh) scripts/place_labels.py board.kicad_pcb
"""

import sys

import pcbnew


TEXT = 1.0        # 部品番号の高さ (mm)
STROKE = 0.15     # 部品番号とシルク線の最小線幅 (mm)
PAD_GAP = 0.15    # シルクとパッド (マスク開口) の間隔。JLCPCB の下限
BODY_GAP = 0.1    # 部品番号と部品本体の間隔
LABEL_GAP = 0.2   # 部品番号どうしの間隔
EDGE_GAP = 0.3    # 部品番号と基板の縁の間隔
STEP = 0.25       # 候補位置の刻み


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def box(r) -> tuple:
    return (pcbnew.ToMM(r.GetLeft()), pcbnew.ToMM(r.GetTop()),
            pcbnew.ToMM(r.GetRight()), pcbnew.ToMM(r.GetBottom()))


def merge(boxes) -> tuple:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def hits(a, b, gap: float) -> bool:
    return (a[0] < b[2] + gap and b[0] < a[2] + gap
            and a[1] < b[3] + gap and b[1] < a[3] + gap)


def candidates(body, w, h):
    """本体の周りの候補 (中心 x, y, 角度, コスト)。近くて 0 度のものほど安い。"""
    l, t, r, b = body
    cx, cy = (l + r) / 2, (t + b) / 2
    out = []
    for angle in (0, 90):
        lw, lh = (w, h) if angle == 0 else (h, w)
        for ring, gap in enumerate((BODY_GAP + 0.05, 0.5, 1.0, 1.6)):
            sides = (
                (cx, t - gap - lh / 2, "x", r - l),   # 上
                (cx, b + gap + lh / 2, "x", r - l),   # 下
                (l - gap - lw / 2, cy, "y", b - t),   # 左
                (r + gap + lw / 2, cy, "y", b - t),   # 右
            )
            for x0, y0, axis, span in sides:
                reach = span / 2 + max(lw, lh) / 2
                n = int(reach / STEP)
                for k in range(-n, n + 1):
                    x, y = (x0 + k * STEP, y0) if axis == "x" else (x0, y0 + k * STEP)
                    cost = ring * 2.0 + abs(k) * STEP + (0.6 if angle else 0)
                    out.append((x, y, angle, lw, lh, cost))
    out.sort(key=lambda c: c[5])
    return out


def main(pcb_path: str) -> int:
    board = pcbnew.LoadBoard(pcb_path)
    edges = box(board.GetBoardEdgesBoundingBox())
    inner = (edges[0] + EDGE_GAP, edges[1] + EDGE_GAP, edges[2] - EDGE_GAP, edges[3] - EDGE_GAP)

    # 先に全部読む (pcbnew のオブジェクトを編集した後の参照は当てにならない)
    fps = list(board.GetFootprints())
    pads, bodies, widened = [], {}, 0
    silk = (pcbnew.F_SilkS, pcbnew.B_SilkS)
    outline = silk + (pcbnew.F_Fab, pcbnew.B_Fab, pcbnew.F_CrtYd, pcbnew.B_CrtYd)
    for fp in fps:
        ref = fp.GetReference()
        parts = []
        for p in fp.Pads():
            pb = box(p.GetBoundingBox())
            pads.append((ref, pb))
            parts.append(pb)
        for g in fp.GraphicalItems():
            if g.GetClass() == "PCB_SHAPE" and g.GetLayer() in outline:
                parts.append(box(g.GetBoundingBox()))
                if g.GetLayer() in silk and g.GetWidth() < mm(STROKE):
                    g.SetWidth(mm(STROKE))
                    widened += 1
        if parts:
            bodies[ref] = merge(parts)

    # 部品番号の大きさを揃え、中央揃えにしてから寸法を測る
    labels = {}
    for fp in fps:
        fp.Value().SetVisible(False)
        t = fp.Reference()
        if not t.IsVisible() or fp.GetReference() not in bodies:
            continue
        t.SetLayer(pcbnew.F_SilkS if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(TEXT), mm(TEXT)))
        t.SetTextThickness(mm(STROKE))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        t.SetTextAngleDegrees(0)
        tb = box(t.GetBoundingBox())
        labels[fp.GetReference()] = (fp, tb[2] - tb[0], tb[3] - tb[1])

    def free(ref, c, placed) -> bool:
        x, y, _, lw, lh, _ = c
        lb = (x - lw / 2, y - lh / 2, x + lw / 2, y + lh / 2)
        if lb[0] < inner[0] or lb[1] < inner[1] or lb[2] > inner[2] or lb[3] > inner[3]:
            return False
        if any(hits(lb, pb, PAD_GAP) for _, pb in pads):
            return False
        if any(hits(lb, bb, BODY_GAP) for r, bb in bodies.items()):
            return False
        return not any(hits(lb, ob, LABEL_GAP) for ob in placed)

    options = {ref: candidates(bodies[ref], w, h) for ref, (_, w, h) in labels.items()}
    room = {ref: sum(1 for c in cs if free(ref, c, [])) for ref, cs in options.items()}
    placed, moved, fab = [], 0, []
    for ref in sorted(labels, key=lambda r: (room[r], r)):
        fp = labels[ref][0]
        t = fp.Reference()
        pick = next((c for c in options[ref] if free(ref, c, placed)), None)
        if pick is None:
            t.SetLayer(pcbnew.F_Fab if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_Fab)
            t.SetPosition(fp.GetPosition())
            fab.append(ref)
            continue
        x, y, angle, lw, lh, _ = pick
        t.SetTextAngleDegrees(angle)
        t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        placed.append((x - lw / 2, y - lh / 2, x + lw / 2, y + lh / 2))
        moved += 1

    board.Save(pcb_path)
    print(f"placed {moved} reference label(s) at {TEXT}mm, widened {widened} thin silk line(s)")
    if fab:
        print(f"no room on silkscreen, moved to Fab: {', '.join(sorted(fab))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
