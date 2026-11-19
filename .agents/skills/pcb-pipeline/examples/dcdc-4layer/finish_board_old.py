"""DC-DC 基板の、atopile では書けない部分を 2 段で仕上げる。

pre  (自動配線の前)
  * 重複した uuid の振り直し (atopile はパッドの uuid を部品間で使い回す)
  * 4 層化。In1/In2 は電源層扱い (ルータは信号を引かない) の GND 面
  * M3 取付穴 4 つ
  * パワー段の銅: VIN, SW, IL_P, VOUT を F.Cu のゾーンで作る
  * 手で決めて固定する配線 (ロックするのでルータは触らない)
      - シャントのケルビン線 2 本
      - ゲート: ゲートパッド -> ビア -> B.Cu で SW の帯の下 -> ビア -> 4.7Ω / 1Ω -> ドライバ
      - TS, BST, ドライバ VCC, INP, OVLO の短い線
  * 固定 GND ビアと、GND の表面実装パッドごとのファンアウト (ビア + 短い線)
  * 配線中だけの禁止領域: パワー段のベタの上、ケルビン線の間、基板の縁
    (Freerouting は信号層上のベタを他ネットの障害物として扱わない)

post (セッションを取り込んだ後)
  * 配線用の禁止領域を外す
  * ルータが残す重複片と行き止まりの配線片、穴間隔を割る GND ビアを消す
  * F.Cu と B.Cu の GND ベタ。ビアの届かない島は捨てる
  * 表裏の GND ベタがともに十分広い所に GND ステッチングビアを打つ

どちらも何度流してもよい。前回足したものを先に消してから足し直す。
消去は別プロセスで行う (同じプロセスで基板を読み直すと SWIG のラッパが壊れる)。

  $(scripts/kicad_python.sh) scripts/finish_board.py board.kicad_pcb pre|post
"""

import os
import sys

import pcbnew

TAG = "dcdc"
HOLE_LIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty"
HOLE_FP = "MountingHole_3.2mm_M3_DIN965"
HOLES = [(-37.0, -27.2), (37.0, -27.2), (-37.0, 27.2), (37.0, 27.2)]
EDGE_INSET = 0.5  # ベタを基板端から離す距離

# ---- パワー段のゾーン (F.Cu)。座標は placement_default.txt の配置に合わせてある
POWER_ZONES = {
    # 入力端子 (上のピン) -> 左上一帯 -> Q のドレインと Cin の左パッド。
    # 左端の細い帯でバルクコンデンサの + と VIN タップの 0Ω まで下りる
    "VIN": [
        (-39.5, -3.9), (-39.5, -23.8), (-33.6, -23.8), (-33.6, -29.4),
        (-15.0, -29.4), (-15.0, -22.1), (-17.0, -22.1), (-17.0, -20.35),
        (-23.3, -20.35), (-23.3, -17.75), (-29.0, -17.75), (-29.0, -18.0),
        (-37.5, -18.0), (-37.5, -3.9),
    ],
    # Q のソース -> D のカソード -> インダクタ左パッドの帯。上下の幅は Q のソース列と
    # D のカソードの分だけ。左下はブートストラップ C の SW パッドまでの小さな張り出し
    "SW": [
        (-22.6, -20.0), (-8.3, -20.0), (-8.3, -23.5), (-3.7, -23.5),
        (-3.7, -10.5), (-8.3, -10.5), (-8.3, -14.2), (-20.9, -14.2),
        (-20.9, -12.6), (-22.7, -12.6), (-22.7, -14.2), (-22.6, -14.2),
    ],
    # インダクタ右パッド -> シャント左パッド。ケルビン線の通り道 (x 15..18) は含めない
    "IL_P": [(7.7, -23.5), (14.7, -23.5), (14.7, -10.5), (7.7, -10.5)],
    # シャント右パッド -> 出力コンデンサ + -> 出力端子。右上の取付穴は避ける
    "VOUT": [
        (18.3, -13.0), (18.3, -29.0), (33.5, -29.0), (33.5, -23.6),
        (39.5, -23.6), (39.5, -19.4), (31.3, -19.4), (31.3, -22.5),
        (25.5, -22.5), (25.5, -13.0),
    ],
}

# ---- 配線中だけ置く F.Cu の禁止領域 (post で外す)。パワー段のベタの輪郭にも置く
ROUTE_KEEPOUTS = {
    # ケルビン線 2 本の間とその周り。他の信号を割り込ませない
    "kelvin": [(14.9, -18.9), (18.1, -18.9), (18.1, -11.0), (14.9, -11.0)],
}
EDGE_KEEPOUT = 0.6

# ---- 固定配線: (ネット, 幅 mm, [点...], 層)。層を省くと F.Cu
FIXED_TRACKS = [
    # ケルビン線。パッド中心の高さでパッド内側の縁から出て、隙間を並走して下へ
    ("IL_P", 0.3, [(14.2, -17.0), (15.9, -17.0), (15.9, -11.95)]),
    ("VOUT", 0.3, [(18.8, -17.0), (17.1, -17.0), (17.1, -11.95)]),
    # ゲート: Q のゲートパッドは SW の帯の中にあるので、真下のビアで B.Cu に落とし、
    # 帯の下をくぐってドライバ側のビアで上がる。ゲートループは経路 x 板厚
    ("GATE", 0.4, [(-18.1, -19.12), (-18.1, -17.7)]),
    ("GATE", 0.4, [(-18.1, -17.7), (-16.5, -16.1), (-16.5, -13.6)], "B"),
    ("GATE", 0.4, [(-18.7, -13.85), (-17.5, -13.85), (-16.5, -13.6)]),
    ("GATE", 0.3, [(-16.5, -13.6), (-16.35, -12.2)]),
    ("TGUP", 0.28, [(-19.1, -11.4), (-19.1, -12.1)]),
    ("TGDN", 0.28, [(-18.6, -11.4), (-18.6, -11.55), (-17.5, -11.55), (-17.5, -11.95)]),
    # G-S 抵抗の SW 側を帯へ
    ("SW", 0.4, [(-14.85, -12.2), (-14.85, -14.5)]),
    # TS はドライバから真上の SW の帯へ
    ("SW", 0.28, [(-19.6, -11.4), (-19.6, -14.5)]),
    # BST: ドライバ -> ブートストラップ C -> BST ダイオード
    ("BST", 0.28, [(-20.1, -11.4), (-20.1, -11.8), (-21.3, -11.8)]),
    ("BST", 0.4, [(-21.8, -11.0), (-21.8, -9.9)]),
    # VCC: ドライバ -> BST ダイオード -> 1uF
    ("VCC12", 0.3, [(-20.6, -6.6), (-21.5, -6.6)]),
    ("VCC12", 0.4, [(-21.8, -6.1), (-21.8, -5.3)]),
    # ドライバの GND ピン (3) を裏面パッドへ
    ("GND", 0.28, [(-19.6, -7.0), (-19.6, -7.6)]),
    # INP: ドライバの INP ピンから真下の AND の出力へ
    ("INP", 0.3, [(-19.1, -5.55), (-19.1, -2.8)]),
    # OVLO: ドライバのピンから真下の 1nF へ
    ("OVLO", 0.25, [(-18.6, -5.55), (-18.0, -4.8)]),
    # INA241 の REF1 (7) は両隣に挟まれてビアが打てない。腹の下を通して GND (2) へ
    ("GND", 0.25, [(17.76, -6.62), (15.24, -6.62)]),
]

# ---- ネット付きの固定ビア (GND 以外)
NET_VIAS = [
    ("GATE", -18.1, -17.7),
    ("GATE", -16.5, -13.6),
]

# ---- B.Cu の固定配線: ロジック部 (ドライバの隣) から制御部へ下りる 4 本。
# インダクタの下を F.Cu で通すと SW パッドの横を並走するので、上下にビアを置いて
# B.Cu で抜ける。B.Cu は内層の GND 面 2 枚で SW から遮蔽される。
# (F.Cu に禁止領域を置いて B.Cu へ追いやると、Freerouting 2.1.0 は B.Cu の配線を
#  SES に書き出さずに落とす)
BCU_CORRIDORS = []

# ---- 固定 GND ビア
FIXED_VIAS = [
    # ドライバ裏面パッドの放熱と GND 接続
    (-20.1, -8.4), (-19.1, -8.4),
    # ホットループの GND: Cin の右パッドの右、ドレインとアノードの間
    (-11.8, -23.6), (-11.8, -25.8), (-11.8, -27.8), (-11.2, -21.0), (-16.2, -21.0),
    # スナバ C の GND
    (-8.6, -26.5),
    # 出力コンデンサと 10uF の GND
    (30.0, -17.4), (28.9, -17.4), (31.1, -17.4), (27.4, -17.4),
    # 出力端子の GND の周り
    (33.4, -16.0), (33.4, -14.6),
]


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def pt(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(x), mm(y))


def poly(points) -> pcbnew.VECTOR_VECTOR2I:
    v = pcbnew.VECTOR_VECTOR2I()
    for x, y in points:
        v.append(pt(x, y))
    return v


def clear_previous(pcb_path: str, stage: str) -> int:
    """前回このスクリプトが足したものを消して保存する。

    消すものを全部集めてから消す。編集を始めると pcbnew のラッパが死ぬので、
    足す作業は保存し直した基板を読み込み直してから行う。
    """
    board = pcbnew.LoadBoard(pcb_path)
    doomed = []
    for z in board.Zones():
        name = z.GetZoneName() or ""
        if not name.startswith(TAG + "-"):
            continue
        is_outer = name.startswith(TAG + "-gnd-outer")
        is_keepout = name.startswith(TAG + "-route-keepout")
        # 配線用の禁止領域は post で外す (固定配線の端がベタの中にあるので DRC に掛かる)
        # pre は全部消す (前回の表裏 GND ベタが残ると DSN に面として載り、ルータが詰まる)
        if stage == "pre" or is_outer or is_keepout:
            doomed.append(z)
    if stage == "pre":
        doomed += [t for t in board.GetTracks() if t.IsLocked()]
        doomed += [f for f in board.GetFootprints() if f.GetReference().startswith("MH")]
    else:
        # ステッチングビアはロックせずに打つ。GND の配線の端に繋がっていない
        # ロック無しの GND ビアがそれ (ルータのビアは必ず配線の端にある)
        ends = set()
        for tr in board.GetTracks():
            if tr.GetClass() == "PCB_TRACK" and tr.GetNetname() == "GND":
                for q in (tr.GetStart(), tr.GetEnd()):
                    ends.add((round(pcbnew.ToMM(q.x), 2), round(pcbnew.ToMM(q.y), 2)))
        for tr in board.GetTracks():
            if tr.GetClass() != "PCB_VIA" or tr.IsLocked() or tr.GetNetname() != "GND":
                continue
            q = tr.GetPosition()
            if (round(pcbnew.ToMM(q.x), 2), round(pcbnew.ToMM(q.y), 2)) not in ends:
                doomed.append(tr)
    if stage == "post":
        # ルータが残す行き止まりの配線片を消す。端が同じネットのパッド・配線の端・
        # ビア・ベタのどれにも触れていなければ行き止まり。消すと別の片が行き止まりに
        # なることがあるので、無くなるまで繰り返す
        def key(q):
            return (round(pcbnew.ToMM(q.x), 3), round(pcbnew.ToMM(q.y), 3))
        pads_by_net = {}
        for pd in board.GetPads():
            pads_by_net.setdefault(pd.GetNetname(), []).append(pd)
        zones_by_net = {}
        for z in board.Zones():
            if not z.GetIsRuleArea():
                zones_by_net.setdefault(z.GetNetname(), []).append(z)
        live = [tr for tr in board.GetTracks() if tr.GetClass() == "PCB_TRACK" and not tr.IsLocked()]
        # ルータは同じ片を往復で 2 本重ねて書くことがある。重なりは 1 本にする
        seen_seg = set()
        for tr in list(live):
            a, b2 = key(tr.GetStart()), key(tr.GetEnd())
            sk = (tr.GetNetname(), tr.GetLayer(), min(a, b2), max(a, b2))
            if sk in seen_seg:
                doomed.append(tr)
                live.remove(tr)
            else:
                seen_seg.add(sk)
        fixed_items = [tr for tr in board.GetTracks() if tr.IsLocked() or tr.GetClass() == "PCB_VIA"]
        while True:
            ends = {}
            for tr in live + [f for f in fixed_items if f.GetClass() == "PCB_TRACK"]:
                for q in (tr.GetStart(), tr.GetEnd()):
                    ends.setdefault((tr.GetNetname(), tr.GetLayer(), key(q)), []).append(tr)
            vias = {(v.GetNetname(), key(v.GetPosition())) for v in fixed_items if v.GetClass() == "PCB_VIA"}
            segs_by = {}
            for tr in live + [f for f in fixed_items if f.GetClass() == "PCB_TRACK"]:
                segs_by.setdefault((tr.GetNetname(), tr.GetLayer()), []).append(tr)

            def on_other_segment(tr, q):
                # 他の片の途中に T 字で繋がっている
                qx, qy = pcbnew.ToMM(q.x), pcbnew.ToMM(q.y)
                for o in segs_by.get((tr.GetNetname(), tr.GetLayer()), []):
                    if o is tr or o == tr:
                        continue
                    s, e2 = o.GetStart(), o.GetEnd()
                    d = seg_point_dist(pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(e2.x), pcbnew.ToMM(e2.y), qx, qy)
                    if d <= pcbnew.ToMM(o.GetWidth()) / 2:
                        return True
                return False

            dangling = []
            for tr in live:
                n, layer = tr.GetNetname(), tr.GetLayer()
                for q in (tr.GetStart(), tr.GetEnd()):
                    k = key(q)
                    if len(ends.get((n, layer, k), [])) > 1 or (n, k) in vias:
                        continue
                    if on_other_segment(tr, q):
                        continue
                    if any(pd.IsOnLayer(layer) and pd.HitTest(q) for pd in pads_by_net.get(n, [])):
                        continue
                    if any(z.IsOnLayer(layer) and z.HitTestFilledArea(layer, q) for z in zones_by_net.get(n, [])):
                        continue
                    dangling.append(tr)
                    break
            if not dangling:
                break
            doomed += dangling
            live = [tr for tr in live if tr not in dangling]
        # ルータは同じネットの穴どうしの間隔を見ないので、GND ビアを固定ビアや
        # 端子の穴のすぐ隣に打つ。穴間 0.25mm を割るルータのビアは捨てる
        # (内層の GND 面に直接繋がるので、消しても接続は変わらない)
        holes = []
        for tr in board.GetTracks():
            if tr.GetClass() == "PCB_VIA":
                q = tr.GetPosition()
                holes.append((tr, pcbnew.ToMM(q.x), pcbnew.ToMM(q.y), pcbnew.ToMM(tr.GetDrillValue()) / 2))
        for fp in board.GetFootprints():
            for pd in fp.Pads():
                if pd.HasHole():
                    q = pd.GetPosition()
                    holes.append((pd, pcbnew.ToMM(q.x), pcbnew.ToMM(q.y), pcbnew.ToMM(pd.GetDrillSize().x) / 2))
        for i, (it, x, y, r) in enumerate(holes):
            if it.GetClass() != "PCB_VIA" or it.IsLocked() or it.GetNetname() != "GND" or it in doomed:
                continue
            for j, (other, x2, y2, r2) in enumerate(holes):
                if i == j or other in doomed:
                    continue
                if ((x - x2) ** 2 + (y - y2) ** 2) ** 0.5 - r - r2 < 0.25:
                    doomed.append(it)
                    break
    for item in doomed:
        board.Remove(item)
    board.Save(pcb_path)
    return len(doomed)


def set_four_layers(board: pcbnew.BOARD) -> str:
    board.SetCopperLayerCount(4)
    for layer in (pcbnew.In1_Cu, pcbnew.In2_Cu):
        board.SetLayerType(layer, pcbnew.LT_POWER)
    board.SetLayerName(pcbnew.In1_Cu, "In1.Cu")
    board.SetLayerName(pcbnew.In2_Cu, "In2.Cu")
    return "4 copper layers, In1/In2 as power (plane) layers"


def add_holes(board: pcbnew.BOARD) -> str:
    for i, (x, y) in enumerate(HOLES, 1):
        fp = pcbnew.FootprintLoad(HOLE_LIB, HOLE_FP)
        fp.SetReference(f"MH{i}")
        fp.SetPosition(pt(x, y))
        attrs = fp.GetAttributes()
        attrs |= pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY
        fp.SetAttributes(attrs)
        board.Add(fp)
    return f"{len(HOLES)} M3 holes"


def add_zone(board, net, layer, points, name, priority, full=True):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetZoneName(name)
    z.AddPolygon(poly(points))
    z.SetAssignedPriority(priority)
    z.SetMinThickness(mm(0.25))
    z.SetLocalClearance(mm(0.2))   # 既定の 0.5mm だとネットクラスの 0.2mm と食い違う
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if full else pcbnew.ZONE_CONNECTION_THERMAL)
    if not full:
        z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.5))
    z.SetIsFilled(False)
    board.Add(z)
    return z


def board_rect(edges, inset=EDGE_INSET):
    l, t, r, b = edges
    return [(l + inset, t + inset), (r - inset, t + inset), (r - inset, b - inset), (l + inset, b - inset)]


def add_track(board, net, width, pts, layer="F"):
    n = 0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pt(x0, y0))
        t.SetEnd(pt(x1, y1))
        t.SetWidth(mm(width))
        t.SetLayer(pcbnew.B_Cu if layer == "B" else pcbnew.F_Cu)
        t.SetNet(net)
        t.SetLocked(True)
        board.Add(t)
        n += 1
    return n


def add_via(board, net, x, y, locked=True, size=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetPosition(pt(x, y))
    v.SetDrill(mm(drill))
    v.SetWidth(mm(size))
    v.SetNet(net)
    v.SetLocked(locked)
    board.Add(v)
    return v


def point_in_poly(x, y, pts) -> bool:
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def seg_point_dist(ax, ay, bx, by, px, py) -> float:
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    cx, cy = ax + t * dx, ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def fanout_gnd(board, gnd, edges, extra_vias) -> tuple:
    """GND の表面実装パッドごとに、すぐ隣へ GND ビアを打って短く繋ぐ。

    内層が GND 面なので、これで GND は配線不要になる。ルータに任せると
    パッドごとのビアを諦めて未配線が数十本残る。
    ビアの位置はパッドの外向き 8 方向から、他ネットのパッド・固定配線・
    パワー段のゾーン・既存ビアに当たらない最初のものを選ぶ。
    """
    CLR = 0.25          # 他ネットとの間隔
    VIA_R = 0.3
    TRACK_W = 0.35
    # 障害物: 他ネットのパッド (矩形), 固定配線, ゾーン輪郭
    rects = []
    gnd_pads = []
    for fp in board.GetFootprints():
        fc = fp.GetPosition()
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            r = (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                 pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))
            if p.GetNetname() == "GND":
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.IsOnLayer(pcbnew.F_Cu):
                    gnd_pads.append((fp.GetReference(), p.GetNumber(), r,
                                     (pcbnew.ToMM(fc.x), pcbnew.ToMM(fc.y))))
            else:
                rects.append(r)
    for fp in board.GetFootprints():
        if fp.GetReference().startswith("MH"):
            c = fp.GetPosition()
            x, y = pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)
            rects.append((x - 3.0, y - 3.0, x + 3.0, y + 3.0))
    segs = []
    for f in FIXED_TRACKS:
        net, w, pts = f[0], f[1], f[2]
        if net == "GND":
            continue
        for a, b in zip(pts, pts[1:]):
            segs.append((a, b, w / 2))
    for net, x, y0, y1 in BCU_CORRIDORS:
        segs.append(((x, y0), (x, y1), 0.125))
    vias = list(extra_vias)
    l, t, r_, b_ = edges

    def rect_dist(r, x, y):
        dx = max(r[0] - x, 0.0, x - r[2])
        dy = max(r[1] - y, 0.0, y - r[3])
        return (dx * dx + dy * dy) ** 0.5

    def clear(vx, vy, px, py) -> bool:
        if not (l + 1.0 < vx < r_ - 1.0 and t + 1.0 < vy < b_ - 1.0):
            return False
        for rc in rects:
            if rect_dist(rc, vx, vy) < VIA_R + CLR:
                return False
            # 引き出し線も他ネットのパッドに触れないこと
            for k in range(0, 25):
                sx = px + (vx - px) * k / 24
                sy = py + (vy - py) * k / 24
                if rect_dist(rc, sx, sy) < TRACK_W / 2 + CLR:
                    return False
        for (ax, ay), (bx, by), hw in segs:
            if seg_point_dist(ax, ay, bx, by, vx, vy) < VIA_R + hw + CLR:
                return False
        for name, pts in POWER_ZONES.items():
            if point_in_poly(vx, vy, pts):
                return False
            for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
                if seg_point_dist(ax, ay, bx, by, vx, vy) < VIA_R + 0.3:
                    return False
        for ox, oy in vias:
            if ((ox - vx) ** 2 + (oy - vy) ** 2) ** 0.5 < 2 * VIA_R + 0.3:
                return False
        return True

    placed, failed = 0, []
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (0.707, 0.707), (-0.707, 0.707), (0.707, -0.707), (-0.707, -0.707)]
    for ref, num, rc, fc in gnd_pads:
        px, py = (rc[0] + rc[2]) / 2, (rc[1] + rc[3]) / 2
        if any(rc[0] <= vx <= rc[2] and rc[1] <= vy <= rc[3] for vx, vy in vias):
            continue  # 既にパッド上にビアがある (裏面パッドなど)
        hx, hy = (rc[2] - rc[0]) / 2, (rc[3] - rc[1]) / 2
        # 部品の外側を向く方向を先に試す
        ox, oy = px - fc[0], py - fc[1]
        order = sorted(dirs, key=lambda d: -(d[0] * ox + d[1] * oy))
        done = False
        for extra in (0.35, 0.6, 1.0, 1.5):
            for dx, dy in order:
                reach = abs(dx) * hx + abs(dy) * hy
                vx, vy = px + dx * (reach + VIA_R + extra), py + dy * (reach + VIA_R + extra)
                if clear(vx, vy, px, py):
                    add_track(board, gnd, TRACK_W, [(px, py), (vx, vy)])
                    add_via(board, gnd, vx, vy)
                    vias.append((vx, vy))
                    placed += 1
                    done = True
                    break
            if done:
                break
        if not done:
            failed.append(f"{ref}.{num}")
    return placed, failed


def pre(pcb_path: str) -> list:
    board = pcbnew.LoadBoard(pcb_path)
    eb = board.GetBoardEdgesBoundingBox()
    edges = (pcbnew.ToMM(eb.GetLeft()), pcbnew.ToMM(eb.GetTop()),
             pcbnew.ToMM(eb.GetRight()), pcbnew.ToMM(eb.GetBottom()))
    nets = {n: board.FindNet(n) for n in set(list(POWER_ZONES) + ["GND"] + [f[0] for f in FIXED_TRACKS])}
    missing = [n for n, v in nets.items() if v is None]
    if missing:
        raise SystemExit(f"nets missing on board: {missing}; run `ato build` first")

    notes = [set_four_layers(board), add_holes(board)]
    for name, pts in POWER_ZONES.items():
        add_zone(board, nets[name], pcbnew.F_Cu, pts, f"{TAG}-{name.lower()}", 5, full=True)
    for layer in (pcbnew.In1_Cu, pcbnew.In2_Cu):
        add_zone(board, nets["GND"], layer, board_rect(edges), f"{TAG}-gnd-{pcbnew.LayerName(layer)}", 0, full=False)
    # Freerouting は信号層上のベタ (plane) を他ネットの障害物として扱わず、
    # VCC12 が SW のベタを横切って二つに割った。配線の間だけ禁止領域で塞ぐ。
    # ベタのネットのパッドは全部ベタか固定配線で繋がっているので、塞いでも困らない
    l, tp, r, b = edges
    e = EDGE_KEEPOUT
    frames = {
        "edge-top": [(l, tp), (r, tp), (r, tp + e), (l, tp + e)],
        "edge-bottom": [(l, b - e), (r, b - e), (r, b), (l, b)],
        "edge-left": [(l, tp), (l + e, tp), (l + e, b), (l, b)],
        "edge-right": [(r - e, tp), (r, tp), (r, b), (r - e, b)],
    }
    for name, pts in list(POWER_ZONES.items()) + list(ROUTE_KEEPOUTS.items()) + list(frames.items()):
        ko = pcbnew.ZONE(board)
        ko.SetIsRuleArea(True)
        ko.SetDoNotAllowTracks(True)
        ko.SetDoNotAllowVias(True)
        ko.SetDoNotAllowZoneFills(False)
        ko.SetDoNotAllowPads(False)
        ko.SetDoNotAllowFootprints(False)
        ko.SetLayer(pcbnew.F_Cu)
        ko.SetZoneName(f"{TAG}-route-keepout-{name.lower()}")
        ko.AddPolygon(poly(pts))
        board.Add(ko)
    notes.append(f"power zones {', '.join(POWER_ZONES)} on F.Cu, GND planes on In1/In2")

    segs = sum(add_track(board, nets[f[0]], f[1], f[2], *(f[3:] or ["F"])) for f in FIXED_TRACKS)
    for n, x, y in NET_VIAS:
        add_via(board, board.FindNet(n), x, y)
    for n, x, y0, y1 in BCU_CORRIDORS:
        net = board.FindNet(n)
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(pt(x, y0))
        tr.SetEnd(pt(x, y1))
        tr.SetWidth(mm(0.25))
        tr.SetLayer(pcbnew.B_Cu)
        tr.SetNet(net)
        tr.SetLocked(True)
        board.Add(tr)
        add_via(board, net, x, y0)
        add_via(board, net, x, y1)
    notes.append(f"{len(BCU_CORRIDORS)} logic nets carried on B.Cu under the inductor")
    for x, y in FIXED_VIAS:
        add_via(board, nets["GND"], x, y)
    notes.append(f"{segs} locked track segments, {len(FIXED_VIAS)} locked GND vias")
    corridor_vias = [(x, y) for _, x, y0, y1 in BCU_CORRIDORS for y in (y0, y1)] + [(x, y) for _, x, y in NET_VIAS]
    placed, failed = fanout_gnd(board, nets["GND"], edges, list(FIXED_VIAS) + corridor_vias)
    notes.append(f"GND fanout: {placed} pads got a via" + (f", no room for {failed}" if failed else ""))

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(pcb_path)
    return notes


def post(pcb_path: str) -> list:
    board = pcbnew.LoadBoard(pcb_path)
    eb = board.GetBoardEdgesBoundingBox()
    edges = (pcbnew.ToMM(eb.GetLeft()), pcbnew.ToMM(eb.GetTop()),
             pcbnew.ToMM(eb.GetRight()), pcbnew.ToMM(eb.GetBottom()))
    gnd = board.FindNet("GND")
    outer = []
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = add_zone(board, gnd, layer, board_rect(edges),
                     f"{TAG}-gnd-outer-{pcbnew.LayerName(layer)}", 0, full=True)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)  # ビアの届かない切れ端は捨てる
        outer.append(z)
    # シルクの部品番号の大きさと置き場所は scripts/place_labels.py が決める

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())

    # 表裏の GND ベタがともにビアの周り (半径 0.9mm) まで埋まっている所に打つ
    stitched = 0
    l, t, r, b = edges
    step = 3.0
    y = t + 2.0
    ring = [(0, 0), (0.9, 0), (-0.9, 0), (0, 0.9), (0, -0.9), (0.64, 0.64), (-0.64, 0.64), (0.64, -0.64), (-0.64, -0.64)]
    fz, bz = outer
    holes = []
    for tr in board.GetTracks():
        if tr.GetClass() == "PCB_VIA":
            q = tr.GetPosition()
            holes.append((pcbnew.ToMM(q.x), pcbnew.ToMM(q.y), pcbnew.ToMM(tr.GetDrillValue()) / 2))
    for fp in board.GetFootprints():
        for pd in fp.Pads():
            if pd.HasHole():
                q = pd.GetPosition()
                holes.append((pcbnew.ToMM(q.x), pcbnew.ToMM(q.y), pcbnew.ToMM(pd.GetDrillSize().x) / 2))

    def far_from_holes(x, y):
        # 同じ GND でも穴どうしは 0.25mm 空ける (ベタの塗りは同ネットの穴を避けない)
        return all(((x - hx) ** 2 + (y - hy) ** 2) ** 0.5 - hr - 0.15 >= 0.3 for hx, hy, hr in holes)

    while y < b - 2.0:
        x = l + 2.0
        while x < r - 2.0:
            ok = all(
                fz.HitTestFilledArea(pcbnew.F_Cu, pt(x + dx, y + dy))
                and bz.HitTestFilledArea(pcbnew.B_Cu, pt(x + dx, y + dy))
                for dx, dy in ring
            )
            if ok and far_from_holes(x, y):
                add_via(board, gnd, x, y, locked=False)
                holes.append((x, y, 0.15))
                stitched += 1
            x += step
        y += step
    filler.Fill(board.Zones())

    # ビアもパッドも無い GND ベタの島に 1 本ずつ打つ。無いと DRC が未接続にする
    via_nets = []
    for tr in board.GetTracks():
        if tr.GetClass() == "PCB_VIA":
            q = tr.GetPosition()
            via_nets.append((pcbnew.ToMM(q.x), pcbnew.ToMM(q.y), tr.GetNetname()))
    gnd_anchor = [(x, y) for x, y, n in via_nets if n == "GND"]
    for fp in board.GetFootprints():
        for pd in fp.Pads():
            if pd.GetNetname() == "GND" and pd.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                q = pd.GetPosition()
                gnd_anchor.append((pcbnew.ToMM(q.x), pcbnew.ToMM(q.y)))
    patched = 0
    for zone, layer in ((fz, pcbnew.F_Cu), (bz, pcbnew.B_Cu)):
        polys = zone.GetFilledPolysList(layer)
        for i in range(polys.OutlineCount()):
            ol = polys.Outline(i)
            if any(ol.PointInside(pt(x, y)) for x, y in gnd_anchor):
                continue
            bb = ol.BBox()
            x0, y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
            x1, y1 = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
            found = None
            yy = y0 + 0.2
            while yy < y1 and found is None:
                xx = x0 + 0.2
                while xx < x1:
                    if all(fz.HitTestFilledArea(pcbnew.F_Cu, pt(xx + dx, yy + dy))
                           and bz.HitTestFilledArea(pcbnew.B_Cu, pt(xx + dx, yy + dy))
                           for dx, dy in ring) and ol.PointInside(pt(xx, yy)) and far_from_holes(xx, yy):
                        found = (xx, yy)
                        break
                    xx += 0.2
                yy += 0.2
            if found:
                add_via(board, gnd, found[0], found[1], locked=False)
                holes.append((found[0], found[1], 0.15))
                gnd_anchor.append(found)
                patched += 1
    filler.Fill(board.Zones())
    board.Save(pcb_path)
    return [f"GND pours on F.Cu and B.Cu", f"{stitched} stitching vias on a {step:.0f} mm grid",
            f"{patched} extra via(s) for GND islands"]


def dedupe_uuids(pcb_path: str) -> int:
    """重複した uuid を振り直す。

    atopile は同じ部品のフットプリントを複数置くとき、パッドの uuid を
    ライブラリのまま使い回す。KiCad の DRC は uuid で違反の相手を引くので、
    ショートやクリアランス違反が全く別の部品のものとして報告される。
    """
    import re
    import uuid

    text = open(pcb_path).read()
    seen = set()
    count = 0

    def repl(m):
        nonlocal count
        u = m.group(1)
        if u in seen:
            count += 1
            return f'(uuid "{uuid.uuid4()}")'
        seen.add(u)
        return m.group(0)

    text = re.sub(r'\(uuid "([0-9a-f-]+)"\)', repl, text)
    if count:
        open(pcb_path, "w").write(text)
    return count


def main(pcb_path: str, stage: str) -> int:
    if stage == "pre":
        n = dedupe_uuids(pcb_path)
        if n:
            print(f"re-issued {n} duplicated uuid(s)")
    # 消去は別プロセスで行う。同じプロセスで基板を読み直すと、編集後の
    # SWIG ラッパが壊れたまま返ってきて何も呼べない
    import subprocess
    r = subprocess.run([sys.executable, __file__, pcb_path, "clear-" + stage],
                       capture_output=True, text=True)
    removed = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "?"
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return r.returncode
    notes = pre(pcb_path) if stage == "pre" else post(pcb_path)
    print(f"stage {stage}: cleared {removed} previous item(s)")
    for n in notes:
        print(f"  {n}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in ("pre", "post", "clear-pre", "clear-post"):
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    if sys.argv[2].startswith("clear-"):
        print(clear_previous(sys.argv[1], sys.argv[2][len("clear-"):]))
        code = 0
    else:
        code = main(sys.argv[1], sys.argv[2])
    # pcbnew の SWIG は終了時の後始末で落ちる。書き終えたら後始末なしで抜ける
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
