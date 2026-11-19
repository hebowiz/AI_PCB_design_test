"""finish_board.py と基板ごとの設定ファイルが使う、pcbnew まわりの部品。

層は名前 ("F.Cu", "In1.Cu", "B.Cu") で受け取る。層の数には依存しない。

pcbnew は基板を編集すると既存のラッパが死ぬ (references/pcbnew.md)。
そこで `Ctx` は、編集を始める前にパッド・穴・外形を数値で読んでおき、
自分が足したもの (配線、ビア、ゾーンの輪郭) も Python 側の表に控える。
障害物の判定などはこの表だけで行い、編集後の基板からは読み直さない。

このスキルが足したゾーンは名前の頭で見分ける。

  auto-pcb-pre-*    配線の前に置き、配線の後も残す銅 (電源のベタ、内層の面)
  auto-pcb-keep-*   残し続ける禁止領域 (アンテナの下など)
  auto-pcb-route-*  配線の間だけ置く禁止領域。post で外す
  auto-pcb-post-*   配線の後に置くベタ。unroute.py と pre が剥がす

基板直下 (フットプリントの外) のマスク層の図形も、このスクリプトが管理する
(露出銅の開口)。pre と post の消去段が消す。
"""

import glob
import math
import os
import sys

import pcbnew

TAG = "auto-pcb"
PRE, KEEP, ROUTE, POST = (f"{TAG}-{s}-" for s in ("pre", "keep", "route", "post"))
HOLE_PREFIX = "MH"   # 取付穴の部品番号


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def to_mm(v: int) -> float:
    return pcbnew.ToMM(v)


def pt(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(x), mm(y))


def poly(points) -> pcbnew.VECTOR_VECTOR2I:
    v = pcbnew.VECTOR_VECTOR2I()
    for x, y in points:
        v.append(pt(x, y))
    return v


def rect(x0: float, y0: float, x1: float, y1: float) -> list:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def circle(cx: float, cy: float, r: float, segments: int = 192) -> list:
    return [(cx + r * math.cos(2 * math.pi * i / segments),
             cy + r * math.sin(2 * math.pi * i / segments)) for i in range(segments)]


def box(r) -> tuple:
    """pcbnew の BOX2I を (左, 上, 右, 下) mm にする。BOX2I は持ち回らない。"""
    return (to_mm(r.GetLeft()), to_mm(r.GetTop()), to_mm(r.GetRight()), to_mm(r.GetBottom()))


def point_in_poly(x: float, y: float, pts) -> bool:
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


def rect_dist(r, x, y) -> float:
    dx = max(r[0] - x, 0.0, x - r[2])
    dy = max(r[1] - y, 0.0, y - r[3])
    return (dx * dx + dy * dy) ** 0.5


def footprint_dir() -> str:
    """KiCad 同梱のフットプリントライブラリの場所。KICAD_FOOTPRINT_DIR で差し替える。"""
    env = [os.environ.get(k) for k in ("KICAD_FOOTPRINT_DIR", "KICAD10_FOOTPRINT_DIR", "KICAD9_FOOTPRINT_DIR")]
    candidates = [e for e in env if e] + [
        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
        "/usr/share/kicad/footprints",
        "/usr/local/share/kicad/footprints",
    ] + sorted(glob.glob("C:/Program Files/KiCad/*/share/kicad/footprints"), reverse=True)
    for d in candidates:
        if os.path.isdir(d):
            return d
    raise SystemExit("KiCad footprint library not found; set KICAD_FOOTPRINT_DIR")


def copper_names(board) -> list:
    """有効な銅層の名前。表から裏の順。"""
    return [board.GetLayerName(l) for l in board.GetEnabledLayers().CuStack()]


def set_copper_layers(board, count: int, planes=()) -> str:
    """銅層の数を決め、planes に挙げた内層を電源層 (ルータが信号を引かない面) にする。"""
    if count < 2 or count % 2:
        raise SystemExit(f"copper layer count must be even and >= 2, got {count}")
    board.SetCopperLayerCount(count)
    names = copper_names(board)
    inner = names[1:-1]
    bad = [p for p in planes if p not in inner]
    if bad:
        raise SystemExit(f"planes must be inner layers of a {count}-layer board {inner}, got {bad}")
    for name in inner:
        lid = board.GetLayerID(name)
        board.SetLayerType(lid, pcbnew.LT_POWER if name in planes else pcbnew.LT_SIGNAL)
    kinds = ", ".join(f"{n}={'plane' if n in planes else 'signal'}" for n in names)
    return f"{count} copper layers: {kinds}"


class Ctx:
    """編集前に読んだ基板の数値と、このスクリプトが足したものの控え。"""

    def __init__(self, board):
        self.board = board
        self.edges = box(board.GetBoardEdgesBoundingBox())
        self.copper = copper_names(board)
        self.notes = []
        # パッド: 部品番号, 番号, ネット, 外接矩形, 部品中心, SMD か, 載っている銅層, 穴の半径
        self.pads = []
        for fp in board.GetFootprints():
            fc = fp.GetPosition()
            for p in fp.Pads():
                hole = to_mm(p.GetDrillSize().x) / 2 if p.HasHole() else 0.0
                self.pads.append(dict(
                    ref=fp.GetReference(), num=p.GetNumber(), net=p.GetNetname(),
                    rect=box(p.GetBoundingBox()), center=(to_mm(p.GetPosition().x), to_mm(p.GetPosition().y)),
                    fp_center=(to_mm(fc.x), to_mm(fc.y)),
                    smd=p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD,
                    pth=p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH,
                    layers=[n for n in self.copper if p.IsOnLayer(board.GetLayerID(n))],
                    hole=hole))
        # 穴: (x, y, 半径, ネット)。ビアと穴のあるパッド
        self.holes = [(p["center"][0], p["center"][1], p["hole"], p["net"]) for p in self.pads if p["hole"]]
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                q = t.GetPosition()
                self.holes.append((to_mm(q.x), to_mm(q.y), to_mm(t.GetDrillValue()) / 2, t.GetNetname()))
        self.mount = []                # 取付穴 (x, y, 避ける半径)
        for fp in board.GetFootprints():
            if fp.GetReference().startswith(HOLE_PREFIX):
                c = fp.GetPosition()
                self.mount.append((to_mm(c.x), to_mm(c.y), 3.0))
        self.tracks = []               # (ネット, 幅, [点], 層)
        self.vias = []                 # (ネット, x, y, 半径)
        self.copper_polys = []         # (ネット, 層, [点]) 足した銅ゾーンの輪郭
        self.pours = {}                # ネット -> [(層, ZONE)]  post のベタ
        self._nets = {}

    # ---- 参照 ----
    def net(self, name: str):
        if name not in self._nets:
            n = self.board.FindNet(name)
            if n is None:
                raise SystemExit(f"net {name} is not on the board; run `ato build` (or the front end) first")
            self._nets[name] = n
        return self._nets[name]

    def layer(self, name: str) -> int:
        lid = self.board.GetLayerID(name)
        if lid < 0:
            raise SystemExit(f"no layer named {name}")
        return lid

    def layer_set(self, names) -> pcbnew.LSET:
        s = pcbnew.LSET()
        for n in names:
            s.AddLayer(self.layer(n))
        return s

    def inset(self, d: float) -> list:
        l, t, r, b = self.edges
        return rect(l + d, t + d, r - d, b - d)

    def signal_layers(self) -> list:
        """ルータが信号を引く銅層 (電源層を除く)。"""
        b = self.board
        return [n for n in self.copper if b.GetLayerType(b.GetLayerID(n)) != pcbnew.LT_POWER]

    # ---- 足す ----
    def zone(self, net: str, layer: str, points, name: str, priority: int = 0, thermal: bool = False,
             clearance: float = 0.2, min_width: float = 0.25, remove_islands: bool = False):
        """銅のゾーン。name は PRE / POST などの頭を付けて渡す。"""
        z = pcbnew.ZONE(self.board)
        z.SetLayer(self.layer(layer))
        z.SetNet(self.net(net))
        z.SetZoneName(name)
        z.AddPolygon(poly(points))
        z.SetAssignedPriority(priority)
        z.SetMinThickness(mm(min_width))
        z.SetLocalClearance(mm(clearance))   # 既定の 0.5mm はネットクラスとずれる
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
        if thermal:
            z.SetThermalReliefGap(mm(0.3))
            z.SetThermalReliefSpokeWidth(mm(0.5))
        if remove_islands:
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetIsFilled(False)
        self.board.Add(z)
        self.copper_polys.append((net, layer, list(points)))
        return z

    def keepout(self, layers, points, name: str, tracks=True, vias=True, fills=False, pads=False):
        """ルールエリア。fills=True で銅ゾーンの塗りも禁じる。"""
        ko = pcbnew.ZONE(self.board)
        ko.SetIsRuleArea(True)
        ko.SetDoNotAllowTracks(tracks)
        ko.SetDoNotAllowVias(vias)
        ko.SetDoNotAllowZoneFills(fills)
        ko.SetDoNotAllowPads(pads)
        ko.SetDoNotAllowFootprints(False)
        ko.SetLayerSet(self.layer_set(layers))
        ko.SetZoneName(name)
        ko.AddPolygon(poly(points))
        self.board.Add(ko)
        return ko

    def track(self, net: str, width: float, pts, layer: str = "F.Cu", locked: bool = True) -> int:
        n = 0
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(self.board)
            t.SetStart(pt(x0, y0))
            t.SetEnd(pt(x1, y1))
            t.SetWidth(mm(width))
            t.SetLayer(self.layer(layer))
            t.SetNet(self.net(net))
            t.SetLocked(locked)
            self.board.Add(t)
            n += 1
        self.tracks.append((net, width, list(pts), layer))
        return n

    def via(self, net: str, x: float, y: float, size: float = 0.6, drill: float = 0.3, locked: bool = True):
        v = pcbnew.PCB_VIA(self.board)
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetPosition(pt(x, y))
        v.SetDrill(mm(drill))
        v.SetWidth(mm(size))
        v.SetNet(self.net(net))
        v.SetLocked(locked)
        self.board.Add(v)
        self.vias.append((net, x, y, size / 2))
        self.holes.append((x, y, drill / 2, net))
        return v

    def mounting_holes(self, at, footprint: str = "MountingHole_3.2mm_M3_DIN965",
                       library: str = "MountingHole.pretty") -> str:
        lib = os.path.join(footprint_dir(), library)
        for i, (x, y) in enumerate(at, 1):
            fp = pcbnew.FootprintLoad(lib, footprint)
            if fp is None:
                raise SystemExit(f"{footprint} not found in {lib}")
            fp.SetReference(f"{HOLE_PREFIX}{i}")
            fp.SetPosition(pt(x, y))
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM
                             | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
            self.board.Add(fp)
            self.mount.append((x, y, 3.0))
        return f"{len(at)} mounting hole(s) {footprint}"

    def mask_ring(self, cx: float, cy: float, r_in: float, r_out: float, layers=("F.Mask", "B.Mask")) -> None:
        """円環のソルダマスク開口 (露出銅)。線幅付きの円で描く。"""
        for name in layers:
            ring = pcbnew.PCB_SHAPE(self.board)
            ring.SetShape(pcbnew.SHAPE_T_CIRCLE)
            ring.SetLayer(self.layer(name))
            ring.SetCenter(pt(cx, cy))
            ring.SetEnd(pt(cx + (r_in + r_out) / 2, cy))
            ring.SetWidth(mm(r_out - r_in))
            ring.SetFilled(False)
            self.board.Add(ring)

    def mask_opening(self, points, layers=("F.Mask",)) -> None:
        """多角形のソルダマスク開口。"""
        for name in layers:
            s = pcbnew.PCB_SHAPE(self.board)
            s.SetShape(pcbnew.SHAPE_T_POLY)
            s.SetLayer(self.layer(name))
            s.SetPolyPoints(poly(points))
            s.SetFilled(True)
            s.SetWidth(0)
            self.board.Add(s)

    def pour(self, net: str, layers, points=None, name: str = "", priority: int = 0, inset: float = 0.5) -> list:
        """配線の後のベタ。points を省くと基板の外接矩形から inset 内側。"""
        pts = points or self.inset(inset)
        zones = []
        for layer in layers:
            z = self.zone(net, layer, pts, f"{POST}{name or net.lower()}-{layer}", priority,
                          remove_islands=True)
            self.pours.setdefault(net, []).append((layer, z))
            zones.append(z)
        return zones

    def fill(self) -> None:
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())


# --------------------------------------------------------------------------
# 配線前: 面に落とすネットのファンアウト
# --------------------------------------------------------------------------
def fanout(ctx: Ctx, net: str, layers=("F.Cu",), clearance: float = 0.25, via_size: float = 0.6,
           via_drill: float = 0.3, width: float = 0.35, edge: float = 1.0):
    """net の表面実装パッドごとに、すぐ隣へビアを打って短く繋ぎ、ロックする。

    内層にそのネットの面があるとき、これで配線が要らなくなる。ルータに任せると
    パッドごとのビアを打ちきれず、未配線が数十本残る。ビアの位置はパッドの外向き
    8 方向と距離を順に試し、他ネットのパッド・足した配線・足した銅ゾーン・既存の
    ビア・取付穴・基板の縁のどれにも当たらない最初の点を選ぶ。
    """
    via_r = via_size / 2
    rects = [p["rect"] for p in ctx.pads if p["net"] != net]
    rects += [(x - r, y - r, x + r, y + r) for x, y, r in ctx.mount]
    segs = [(a, b, w / 2) for n, w, pts, _ in ctx.tracks if n != net for a, b in zip(pts, pts[1:])]
    polys = [pts for n, layer, pts in ctx.copper_polys if layer in layers and n != net]
    # 既存のビアは見ない。pre の時点で残っているのは unroute で剥がす前回の配線のもの
    vias = [(x, y) for _, x, y, _ in ctx.vias] + [p["center"] for p in ctx.pads if p["hole"]]
    l, t, r_, b_ = ctx.edges

    def clear(vx, vy, px, py) -> bool:
        if not (l + edge < vx < r_ - edge and t + edge < vy < b_ - edge):
            return False
        for rc in rects:
            if rect_dist(rc, vx, vy) < via_r + clearance:
                return False
            for k in range(25):   # 引き出し線も他ネットのパッドに触れないこと
                sx, sy = px + (vx - px) * k / 24, py + (vy - py) * k / 24
                if rect_dist(rc, sx, sy) < width / 2 + clearance:
                    return False
        for (ax, ay), (bx, by), hw in segs:
            if seg_point_dist(ax, ay, bx, by, vx, vy) < via_r + hw + clearance:
                return False
        for pts in polys:
            if point_in_poly(vx, vy, pts):
                return False
            for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
                if seg_point_dist(ax, ay, bx, by, vx, vy) < via_r + 0.3:
                    return False
        return all(((ox - vx) ** 2 + (oy - vy) ** 2) ** 0.5 >= 2 * via_r + 0.3 for ox, oy in vias)

    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1),
            (0.707, 0.707), (-0.707, 0.707), (0.707, -0.707), (-0.707, -0.707)]
    placed, failed = 0, []
    for p in ctx.pads:
        on = [n for n in p["layers"] if n in layers]
        if p["net"] != net or not p["smd"] or not on:
            continue
        rc = p["rect"]
        if any(rc[0] <= vx <= rc[2] and rc[1] <= vy <= rc[3] for vx, vy in vias):
            continue   # 既にパッドの上にビアがある (裏面パッドなど)
        px, py = (rc[0] + rc[2]) / 2, (rc[1] + rc[3]) / 2
        hx, hy = (rc[2] - rc[0]) / 2, (rc[3] - rc[1]) / 2
        ox, oy = px - p["fp_center"][0], py - p["fp_center"][1]
        order = sorted(dirs, key=lambda d: -(d[0] * ox + d[1] * oy))   # 部品の外向きから
        done = False
        for extra in (0.35, 0.6, 1.0, 1.5):
            for dx, dy in order:
                reach = abs(dx) * hx + abs(dy) * hy + via_r + extra
                vx, vy = px + dx * reach, py + dy * reach
                if clear(vx, vy, px, py):
                    ctx.track(net, width, [(px, py), (vx, vy)], on[0])
                    ctx.via(net, vx, vy, via_size, via_drill)
                    vias.append((vx, vy))
                    placed += 1
                    done = True
                    break
            if done:
                break
        if not done:
            failed.append(f"{p['ref']}.{p['num']}")
    return placed, failed


# --------------------------------------------------------------------------
# 配線後: ステッチングと島
# --------------------------------------------------------------------------
RING = [(0, 0), (0.9, 0), (-0.9, 0), (0, 0.9), (0, -0.9),
        (0.64, 0.64), (-0.64, 0.64), (0.64, -0.64), (-0.64, -0.64)]


def _filled_everywhere(ctx: Ctx, zones, x: float, y: float) -> bool:
    return all(z.HitTestFilledArea(ctx.layer(layer), pt(x + dx, y + dy))
               for layer, z in zones for dx, dy in RING)


def _far_from_holes(ctx: Ctx, x: float, y: float, gap: float) -> bool:
    # 同じネットでも穴どうしは空ける (ベタの塗りは同ネットの穴を避けない)
    return all(((x - hx) ** 2 + (y - hy) ** 2) ** 0.5 - hr - 0.15 >= gap for hx, hy, hr, _ in ctx.holes)


def stitch(ctx: Ctx, net: str, pitch: float = 3.0, margin: float = 2.0, hole_gap: float = 0.3) -> int:
    """net のベタがすべての層で埋まっている格子点にビアを打つ。ロックしない。"""
    zones = ctx.pours.get(net, [])
    if not zones:
        return 0
    l, t, r, b = ctx.edges
    n = 0
    y = t + margin
    while y < b - margin:
        x = l + margin
        while x < r - margin:
            if _filled_everywhere(ctx, zones, x, y) and _far_from_holes(ctx, x, y, hole_gap):
                ctx.via(net, x, y, locked=False)
                n += 1
            x += pitch
        y += pitch
    return n


def patch_islands(ctx: Ctx, net: str, hole_gap: float = 0.3, step: float = 0.2) -> int:
    """ビアもスルーホールも無いベタの島に 1 本ずつビアを打つ。無いと DRC が未接続にする。"""
    zones = ctx.pours.get(net, [])
    anchors = [(x, y) for x, y, _, n in ctx.holes if n == net]
    patched = 0
    for layer, zone in zones:
        polys = zone.GetFilledPolysList(ctx.layer(layer))
        for i in range(polys.OutlineCount()):
            ol = polys.Outline(i)
            if any(ol.PointInside(pt(x, y)) for x, y in anchors):
                continue
            x0, y0, x1, y1 = box(ol.BBox())
            found = None
            yy = y0 + step
            while yy < y1 and found is None:
                xx = x0 + step
                while xx < x1:
                    if (ol.PointInside(pt(xx, yy)) and _filled_everywhere(ctx, zones, xx, yy)
                            and _far_from_holes(ctx, xx, yy, hole_gap)):
                        found = (xx, yy)
                        break
                    xx += step
                yy += step
            if found:
                ctx.via(net, found[0], found[1], locked=False)
                anchors.append(found)
                patched += 1
    return patched


# --------------------------------------------------------------------------
# 消去 (別プロセスで呼ぶ)
# --------------------------------------------------------------------------
def _key(q) -> tuple:
    return (round(to_mm(q.x), 3), round(to_mm(q.y), 3))


def router_junk(board, plane_nets=(), hole_gap: float = 0.25) -> list:
    """ルータの出力のうち消すもの。

    * 同じ片を往復で 2 本重ねて書いたもの
    * 行き止まりの片。端が同じネットのパッド・片の端・片の途中 (T 字)・ビア・ベタの
      どれにも触れていない片を、無くなるまで繰り返し集める
    * plane_nets のビアで、他の穴との間隔が hole_gap を割るもの (面に直接繋がるので
      消しても接続は変わらない。ルータは同じネットの穴間隔を見ない)
    """
    doomed = []
    pads_by_net = {}
    for pd in board.GetPads():
        pads_by_net.setdefault(pd.GetNetname(), []).append(pd)
    zones_by_net = {}
    for z in board.Zones():
        if not z.GetIsRuleArea():
            zones_by_net.setdefault(z.GetNetname(), []).append(z)
    live = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK" and not t.IsLocked()]
    seen = set()
    for t in list(live):
        a, b = _key(t.GetStart()), _key(t.GetEnd())
        k = (t.GetNetname(), t.GetLayer(), min(a, b), max(a, b))
        if k in seen:
            doomed.append(t)
            live.remove(t)
        else:
            seen.add(k)
    fixed_tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK" and t.IsLocked()]
    vias = {(v.GetNetname(), _key(v.GetPosition())) for v in board.GetTracks() if v.GetClass() == "PCB_VIA"}
    while True:
        ends, segs = {}, {}
        for t in live + fixed_tracks:
            for q in (t.GetStart(), t.GetEnd()):
                ends.setdefault((t.GetNetname(), t.GetLayer(), _key(q)), []).append(t)
            segs.setdefault((t.GetNetname(), t.GetLayer()), []).append(t)

        def on_other(t, q) -> bool:
            qx, qy = to_mm(q.x), to_mm(q.y)
            for o in segs.get((t.GetNetname(), t.GetLayer()), []):
                if o is t or o == t:
                    continue
                s, e = o.GetStart(), o.GetEnd()
                if seg_point_dist(to_mm(s.x), to_mm(s.y), to_mm(e.x), to_mm(e.y), qx, qy) <= to_mm(o.GetWidth()) / 2:
                    return True
            return False

        dangling = []
        for t in live:
            n, layer = t.GetNetname(), t.GetLayer()
            for q in (t.GetStart(), t.GetEnd()):
                k = _key(q)
                if len(ends.get((n, layer, k), [])) > 1 or (n, k) in vias or on_other(t, q):
                    continue
                if any(pd.IsOnLayer(layer) and pd.HitTest(q) for pd in pads_by_net.get(n, [])):
                    continue
                if any(z.IsOnLayer(layer) and z.HitTestFilledArea(layer, q) for z in zones_by_net.get(n, [])):
                    continue
                dangling.append(t)
                break
        if not dangling:
            break
        doomed += dangling
        live = [t for t in live if t not in dangling]

    holes = []
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            q = t.GetPosition()
            holes.append((t, to_mm(q.x), to_mm(q.y), to_mm(t.GetDrillValue()) / 2))
    for pd in board.GetPads():
        if pd.HasHole():
            q = pd.GetPosition()
            holes.append((pd, to_mm(q.x), to_mm(q.y), to_mm(pd.GetDrillSize().x) / 2))
    for i, (it, x, y, r) in enumerate(holes):
        if it.GetClass() != "PCB_VIA" or it.IsLocked() or it.GetNetname() not in plane_nets or it in doomed:
            continue
        for j, (other, x2, y2, r2) in enumerate(holes):
            if i != j and other not in doomed and ((x - x2) ** 2 + (y - y2) ** 2) ** 0.5 - r - r2 < hole_gap:
                doomed.append(it)
                break
    return doomed


def loose_vias(board, nets) -> list:
    """nets のロックしていないビアのうち、配線の端に無いもの (= 前回のステッチング)。

    ルータのビアは必ず配線の端にある。
    """
    ends = set()
    for t in board.GetTracks():
        if t.GetClass() == "PCB_TRACK" and t.GetNetname() in nets:
            ends.add((t.GetNetname(), _key(t.GetStart())))
            ends.add((t.GetNetname(), _key(t.GetEnd())))
    return [v for v in board.GetTracks()
            if v.GetClass() == "PCB_VIA" and not v.IsLocked() and v.GetNetname() in nets
            and (v.GetNetname(), _key(v.GetPosition())) not in ends]


def own_mask_drawings(board) -> list:
    return [d for d in board.GetDrawings() if d.GetLayer() in (pcbnew.F_Mask, pcbnew.B_Mask)]


def exit_now(code: int) -> None:
    """pcbnew の SWIG は終了時の後始末で落ちる。書き終えたら後始末なしで抜ける。"""
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
