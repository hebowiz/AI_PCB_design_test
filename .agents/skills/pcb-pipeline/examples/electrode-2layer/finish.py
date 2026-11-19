"""2 層・ドーナツ電極の微小電流計 (90 x 115 mm, 原点は電極の中心) の仕上げ設定。

  $(scripts/kicad_python.sh) scripts/finish_board.py board.kicad_pcb pre|post board/finish.py

表の定数で書けない部分を pre_hook / post_hook で書く見本。

pre  無線モジュール (U2) のアンテナ下の禁止領域。アンテナはモジュールの外形のうち
     パッドの無い側として見つけるので、モジュールの寸法を書かずに済む
post 円環電極そのもの。半径 RING_OUT_R の円ゾーンを表裏に置き、半径 RING_IN_R の
     ルールエリアで中を抜き、表裏のレジストに円環の開口を開けて銅を露出させる。
     atopile はフットプリントを書き直してカスタムパッドを消すので、電極は
     フットプリントに置けない。あわせて電極より下の帯の裏面にだけ GND ベタ
"""

import pcbkit

LAYERS = 2
EDGE_KEEPOUT = 0      # この基板では無くても縁のクリアランスに掛からなかった

# 露出銅は中央の穴の縁から 0.5mm 手前まで。0.5mm は基板端と銅の最小間隔として一般的な値
RING_IN_R = 15.5
RING_OUT_R = 40.0
ANTENNA_MARGIN = 1.0   # アンテナ端の周りに広げる幅
STRIP_MARGIN = 1.0     # GND ベタを電極の外側から離す距離
GND = "lv"


def pre_hook(ctx):
    module = next((f for f in ctx.board.GetFootprints() if f.GetReference() == "U2"), None)
    if module is None:
        return "no U2, no antenna keep-out"
    left, _, right, bottom = pcbkit.box(module.GetBoundingBox(False, False))
    pad_bottom = max(pcbkit.to_mm(p.GetPosition().y) for p in module.Pads())
    if bottom - pad_bottom < 3.0:
        return "no pad-free module end found, no antenna keep-out"
    m = ANTENNA_MARGIN
    ctx.keepout(["F.Cu", "B.Cu"], pcbkit.rect(left - m, pad_bottom + m, right + m, bottom + m),
                pcbkit.KEEP + "antenna", fills=True)
    return f"antenna keep-out {right - left + 2 * m:.0f} x {bottom - pad_bottom:.0f} mm on both layers"


def post_hook(ctx):
    electrode = next((f for f in ctx.board.GetFootprints() if f.GetReference() == "E1"), None)
    l, t, r, b = ctx.edges
    if electrode is None:
        ctx.pour(GND, ["F.Cu", "B.Cu"])
        return "no E1, GND pour on both faces"
    c = electrode.GetPosition()
    cx, cy = pcbkit.to_mm(c.x), pcbkit.to_mm(c.y)
    net = next((p.GetNetname() for p in electrode.Pads() if p.GetNetname()), None)
    if net is None:
        raise SystemExit("E1 has no net; run `ato build` first")
    for layer in ("F.Cu", "B.Cu"):
        ctx.zone(net, layer, pcbkit.circle(cx, cy, RING_OUT_R), f"{pcbkit.POST}electrode-{layer}", 10)
    ctx.keepout(["F.Cu", "B.Cu"], pcbkit.circle(cx, cy, RING_IN_R), f"{pcbkit.POST}electrode-cutout",
                tracks=False, vias=False, fills=True)
    ctx.mask_ring(cx, cy, RING_IN_R, RING_OUT_R)
    # 電極が表を占めるので、GND は電極より下の帯の裏面だけ
    top = cy + RING_OUT_R + STRIP_MARGIN
    ctx.pour(GND, ["B.Cu"], pcbkit.rect(l, top, r, b), priority=1)
    return f"electrode r{RING_IN_R}..{RING_OUT_R} mm on both faces, GND pour on B.Cu below y={top:.0f}"
