"""回路図を SVG で描くための部品。描いた接続はネット表と 1 ピンずつ突き合わせる。

atopile は回路図を出さない。自動配置のグラフは回路図として読めないので、配置は
基板ごとのスクリプトで手で決める (examples/dcdc-4layer/draw_schematic.py)。
手で保守しないのは正しさのほう。記号を描くたびに、どのパッドをどのネットに
置いたかを宣言させ、`check()` が docs/netlist.md (netlist_diagram.py の出力) と
食い違えば描画を止める。回路を変えると、絵を直すまで通らない。

部品は atopile のインスタンス名 (r_fb_top, drv, ...) で指す。部品番号はレイアウトを
作り直すと振り直されるので、.kicad_pcb の atopile_address から引く。
フロントエンドが atopile でなければ、designators() の代わりに 名前 -> 部品番号 の
表を自分で渡す (部品番号そのものを名前にしてもよい)。

    import schematic as sch
    s = sch.Sheet(1200, 800, sch.designators(pcb), values, notes={"l": "47µH 8.7A"})
    sch.two(s, "R", "r1", (100, 100), (100, 200), "VIN", "FB")
    sch.check(s.pins, nets)
"""

import re
from contextlib import contextmanager
from collections import defaultdict

FG = "#1a1a1a"
ACCENT = "#b03030"
MUTED = "#6a6a6a"
BLOCK = "#2a5a8a"
FONT = "Hiragino Sans, Noto Sans CJK JP, Helvetica Neue, Helvetica, Arial, sans-serif"


# --------------------------------------------------------------------------
# what the board says
# --------------------------------------------------------------------------
def designators(pcb: str) -> dict:
    """atopile address -> designator, from the footprints on the board."""
    out = {}
    for fp in re.split(r"\n\t\(footprint ", open(pcb).read())[1:]:
        ref = re.search(r'\(property "Reference" "([^"]+)"', fp)
        addr = re.search(r'\(property "atopile_address" "([^"]+)"', fp)
        if ref and addr:
            out[addr.group(1)] = ref.group(1)
    return out


def netlist(md: str) -> tuple:
    text = open(md).read()
    rows = re.findall(r"^\| (\w+) \| (.+?) \|$", text, re.M)
    nets = {
        net: sorted(p.strip() for p in pins.split(","))
        for net, pins in rows
        if net != "ネット"
    }
    values = dict(re.findall(r'^\s+(\w+)\["\w+<br/>(.*?)"\]', text, re.M))
    return nets, values


def short_value(ref: str, value: str) -> str:
    m = re.match(r"^([\d.]+\s*[pnµumkM]?[ΩF])", value)
    if not m:
        return value
    out = m.group(1)
    if ref.startswith("C"):
        v = re.search(r"(\d+V)$", value)
        if v:
            out += " " + v.group(1)
    tol = re.search(r"±(0\.\d+)%", value)
    if tol:
        out += f" {tol.group(1)}%"
    return out


# --------------------------------------------------------------------------
# svg primitives
# --------------------------------------------------------------------------
class Sheet:
    def __init__(self, w: int, h: int, refs: dict, values: dict, notes: dict = None):
        """refs: 名前 -> 部品番号, values: 部品番号 -> 値, notes: 名前 -> 値の言い換え"""
        self.w, self.h = w, h
        self.refs, self.values = refs, values
        self.notes = notes or {}
        self.parts: list[str] = []
        self.pins: dict = defaultdict(set)   # net -> {"R5.1", ...}

    # ---- bookkeeping ----
    def ref(self, addr: str) -> str:
        if addr not in self.refs:
            raise SystemExit(f"{addr} is not on the board")
        return self.refs[addr]

    def value(self, addr: str) -> str:
        if addr in self.notes:
            return self.notes[addr]
        ref = self.ref(addr)
        return short_value(ref, self.values.get(ref, ""))

    def pin(self, addr: str, pads: str, net: str) -> None:
        """Declare that the drawing puts these pads of addr on net."""
        for pad in pads.split(","):
            self.pins[net].add(f"{self.ref(addr)}.{pad}")

    # ---- drawing ----
    def add(self, s: str) -> None:
        self.parts.append("  " + s)

    def wire(self, *points, color: str = FG, width: float = 2) -> None:
        pts = " ".join(f"{x},{y}" for x, y in points)
        self.add(
            f'<polyline points="{pts}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
        )

    def dot(self, x: int, y: int) -> None:
        self.add(f'<circle cx="{x}" cy="{y}" r="4" fill="{FG}"/>')

    def text(self, x, y, s, size=13, anchor="start", color=FG, weight="normal"):
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.add(
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>'
        )

    def box(self, x, y, w, h, fill="none", dash=False, color=FG):
        d = ' stroke-dasharray="6 5"' if dash else ""
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" '
            f'fill="{fill}" stroke="{color}" stroke-width="2"{d}/>'
        )

    def block(self, x, y, w, h, title) -> None:
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" '
            f'stroke="{BLOCK}" stroke-width="1.2" stroke-dasharray="4 4" opacity="0.6"/>'
        )
        self.text(x + 12, y + 22, title, 15, color=BLOCK, weight="bold")

    @contextmanager
    def shift(self, dx: int, dy: int = 0):
        """Draw the enclosed symbols moved by (dx, dy)."""
        self.add(f'<g transform="translate({dx},{dy})">')
        yield
        self.add("</g>")

    def render(self) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}">\n'
            f'  <rect width="{self.w}" height="{self.h}" fill="#ffffff"/>\n'
            + "\n".join(self.parts)
            + "\n</svg>\n"
        )


# --------------------------------------------------------------------------
# symbols
# --------------------------------------------------------------------------
def gnd(s: Sheet, x: int, y: int) -> None:
    """Ground: the wire arrives at (x, y) from above."""
    s.wire((x, y), (x, y + 10))
    for i, half in enumerate((14, 9, 4)):
        yy = y + 10 + i * 6
        s.wire((x - half, yy), (x + half, yy))


def flag(s: Sheet, x: int, y: int, name: str) -> None:
    """Supply flag: the wire arrives at (x, y) from below."""
    s.wire((x, y), (x, y - 12))
    s.wire((x - 12, y - 12), (x + 12, y - 12))
    s.text(x, y - 19, name, 12, "middle", ACCENT, "bold")


def label(s: Sheet, x: int, y: int, name: str, anchor="start") -> None:
    """Net label at the loose end of a wire at (x, y)."""
    dx = {"start": 6, "end": -6, "middle": 0}[anchor]
    dy = -8 if anchor == "middle" else 5
    s.text(x + dx, y + dy, name, 12, anchor, ACCENT, "bold")


def two(s: Sheet, kind: str, addr: str, a, b, na: str, nb: str,
        pa="1", pb="2", side="r") -> None:
    """Two-terminal part from a to b (vertical or horizontal).

    Pad pa sits on net na at end a, pad pb on net nb at end b. Diodes point
    from a (anode) to b (cathode).
    """
    s.pin(addr, pa, na)
    s.pin(addr, pb, nb)
    (x0, y0), (x1, y1) = a, b
    vertical = x0 == x1
    sgn = 1 if (y1 > y0 if vertical else x1 > x0) else -1
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    def P(u, v):
        """u along the part (0 = centre, toward b positive), v across it."""
        return (cx + v, cy + sgn * u) if vertical else (cx + sgn * u, cy + v)

    body = {"R": 22, "C": 6, "CP": 6, "L": 30, "D": 11, "TVS": 11, "LED": 11}[kind]
    s.wire(a, P(-body, 0))
    s.wire(P(body, 0), b)
    if kind == "R":
        p, q = P(-22, -11), P(22, 11)
        s.box(min(p[0], q[0]), min(p[1], q[1]), abs(q[0] - p[0]), abs(q[1] - p[1]))
    elif kind in ("C", "CP"):
        s.wire(P(-6, -16), P(-6, 16))
        s.wire(P(6, -16), P(6, 16))
        if kind == "CP":
            px, py = P(-16, -12)
            s.text(px, py + 5, "+", 14, "middle", ACCENT)
    elif kind == "L":
        pts = []
        for i in range(4):
            u0 = -30 + i * 15
            (ax, ay), (mx, my), (ex, ey) = P(u0, 0), P(u0 + 7.5, -12), P(u0 + 15, 0)
            pts.append(f"M {ax} {ay} Q {mx} {my} {ex} {ey}")
        s.add(f'<path d="{" ".join(pts)}" fill="none" stroke="{FG}" stroke-width="2"/>')
    else:
        t1, t2, t3 = P(-11, -12), P(-11, 12), P(11, 0)
        s.add(
            f'<polygon points="{t1[0]},{t1[1]} {t2[0]},{t2[1]} {t3[0]},{t3[1]}" '
            f'fill="{FG}" stroke="{FG}" stroke-width="2"/>'
        )
        s.wire(P(11, -12), P(11, 12))
        if kind == "TVS":
            s.wire(P(11, -12), P(6, -16))
            s.wire(P(11, 12), P(16, 16))
        if kind == "LED":
            for off in (-2, 6):
                p0, p1 = P(off, -14), P(off + 8, -26)
                s.wire(p0, p1, width=1.5)

    ref, val = s.ref(addr), s.value(addr)
    if vertical:
        if side == "r":
            s.text(cx + 22, cy - 3, ref, 13, "start", weight="bold")
            s.text(cx + 22, cy + 13, val, 12, "start", MUTED)
        else:
            s.text(cx - 22, cy - 3, ref, 13, "end", weight="bold")
            s.text(cx - 22, cy + 13, val, 12, "end", MUTED)
    else:
        s.text(cx, cy - 18, ref, 13, "middle", weight="bold")
        s.text(cx, cy + 30, val, 12, "middle", MUTED)


def ic(s: Sheet, addr, x, y, w, h, left=(), right=(), top=(), bottom=(), title=None,
       title_at=None) -> dict:
    """Rectangle with pins. Each pin is (label, offset along the edge, pads, net).

    net None means the pin is left open; it is drawn with an 'NC' mark and
    declares nothing. Returns the outer end of every pin by label.
    """
    s.box(x, y, w, h)
    if any(abs(off - w / 2) < 30 for _, off, _, _ in top):
        s.text(x + w + 8, y - 6, s.ref(addr), 14, "start", weight="bold")
    else:
        s.text(x + w // 2, y - 10, s.ref(addr), 14, "middle", weight="bold")
    tx, ty, ta = title_at or (x + w // 2, y + h + (66 if bottom else 22), "middle")
    s.text(tx, ty, title or s.value(addr), 12, ta, MUTED)
    anchors = {}

    def one(lbl, pads, net, inner, outer, tpos, anchor):
        s.wire(inner, outer)
        s.text(tpos[0], tpos[1], f"{lbl}", 11, anchor, MUTED)
        s.text((inner[0] + outer[0]) / 2 + (0 if inner[0] != outer[0] else 3),
               (inner[1] + outer[1]) / 2 - 4 if inner[0] != outer[0] else (inner[1] + outer[1]) / 2 + 4,
               pads, 9, "middle" if inner[0] != outer[0] else "start", MUTED)
        if net is None:
            ox, oy = outer
            s.wire((ox - 5, oy - 5), (ox + 5, oy + 5))
            s.wire((ox - 5, oy + 5), (ox + 5, oy - 5))
        else:
            s.pin(addr, pads, net)
        anchors[lbl] = outer

    for lbl, off, pads, net in left:
        one(lbl, pads, net, (x, y + off), (x - 18, y + off), (x + 7, y + off + 4), "start")
    for lbl, off, pads, net in right:
        one(lbl, pads, net, (x + w, y + off), (x + w + 18, y + off), (x + w - 7, y + off + 4), "end")
    for lbl, off, pads, net in top:
        one(lbl, pads, net, (x + off, y), (x + off, y - 18), (x + off, y + 16), "middle")
    for lbl, off, pads, net in bottom:
        one(lbl, pads, net, (x + off, y + h), (x + off, y + h + 18), (x + off, y + h - 8), "middle")
    return anchors


def opamp(s: Sheet, addr, x, y, minus_top=False, title=None, unit="") -> dict:
    """Triangle with its left edge at x, centred on y. Returns pin anchors."""
    h, w = 130, 96
    top, bot = y - h // 2, y + h // 2
    s.add(
        f'<polygon points="{x},{top} {x},{bot} {x + w},{y}" fill="none" '
        f'stroke="{FG}" stroke-width="2"/>'
    )
    hi, lo = y - 32, y + 32
    plus, minus = (lo, hi) if minus_top else (hi, lo)
    s.text(x + 10, plus + 6, "+", 17)
    s.text(x + 10, minus + 6, "−", 17)
    s.text(x + 40, top - 4, s.ref(addr) + unit, 13, "start", weight="bold")
    s.text(x + 40, bot + 16, title or s.value(addr), 12, "start", MUTED)
    px = x + w // 4
    edge = (w // 4) * (h // 2) // w
    return {"plus": (x, plus), "minus": (x, minus), "out": (x + w, y),
            "vpos": (px, top + edge), "vneg": (px, bot - edge)}


def nmos(s: Sheet, addr, x, y) -> dict:
    """Vertical N-MOSFET: drain up, source down, gate from the left."""
    s.wire((x - 60, y), (x - 22, y))
    s.wire((x - 22, y - 22), (x - 22, y + 22))
    for y0 in (-24, -6, 12):
        s.wire((x - 12, y + y0), (x - 12, y + y0 + 12))
    s.wire((x - 12, y - 18), (x, y - 18), (x, y - 70))
    s.wire((x - 12, y + 18), (x, y + 18), (x, y + 70))
    s.wire((x - 12, y), (x, y), (x, y + 18))
    s.add(f'<polygon points="{x - 12},{y} {x - 4},{y - 5} {x - 4},{y + 5}" fill="{FG}"/>')
    s.text(x + 14, y - 4, s.ref(addr), 13, weight="bold")
    s.text(x + 14, y + 12, s.value(addr), 12, color=MUTED)
    return {"d": (x, y - 70), "s": (x, y + 70), "g": (x - 60, y)}


def npn(s: Sheet, addr, x, y) -> dict:
    s.wire((x - 40, y), (x - 10, y))
    s.wire((x - 10, y - 22), (x - 10, y + 22))
    s.wire((x - 10, y - 10), (x + 15, y - 30), (x + 15, y - 60))
    s.wire((x - 10, y + 10), (x + 15, y + 30), (x + 15, y + 60))
    s.add(f'<polygon points="{x + 15},{y + 30} {x + 3},{y + 27} {x + 9},{y + 19}" fill="{FG}"/>')
    s.text(x + 24, y - 2, s.ref(addr), 13, weight="bold")
    s.text(x + 24, y + 14, s.value(addr), 12, color=MUTED)
    return {"b": (x - 40, y), "c": (x + 15, y - 60), "e": (x + 15, y + 60)}


def testpoint(s: Sheet, addr, x, y, net, up=True) -> None:
    """Test point on a stub rising from (x, y)."""
    s.pin(addr, "1", net)
    d = -1 if up else 1
    s.wire((x, y), (x, y + d * 28))
    s.add(f'<circle cx="{x}" cy="{y + d * 35}" r="7" fill="#ffffff" stroke="{FG}" stroke-width="2"/>')
    s.text(x + 12, y + d * 35 + 4, s.ref(addr), 11, weight="bold")


def decap(s: Sheet, addr, x, y, net, note) -> None:
    flag(s, x, y, net)
    two(s, "C", addr, (x, y), (x, y + 80), net, "GND")
    gnd(s, x, y + 80)
    s.text(x, y + 124, note, 11, "middle", MUTED)


# --------------------------------------------------------------------------
def check(drawn: dict, nets: dict) -> None:
    """Refuse to draw a schematic that disagrees with the board."""
    drawn = {n: sorted(p) for n, p in drawn.items()}
    if drawn != nets:
        lines = ["the drawing no longer matches the netlist"]
        for n in sorted(set(drawn) | set(nets)):
            a, b = set(nets.get(n, [])), set(drawn.get(n, []))
            if a != b:
                lines.append(f"  {n}: board only {sorted(a - b)}, drawing only {sorted(b - a)}")
        raise SystemExit("\n".join(lines))


def write(sheet, nets: dict, svg_path: str) -> None:
    """照合してから書く。食い違えば SystemExit。"""
    check(sheet.pins, nets)
    open(svg_path, "w").write(sheet.render())
