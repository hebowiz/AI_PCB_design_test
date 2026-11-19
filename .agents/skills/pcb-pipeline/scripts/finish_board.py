"""フロントエンド (atopile など) では書けない基板の仕上げを、設定ファイルに従って 2 段で行う。

  $(scripts/kicad_python.sh) scripts/finish_board.py board.kicad_pcb pre|post board/finish.py

pre  (自動配線の前)
  * 重複した uuid の振り直し
  * 銅層の数と、内層のどれを面 (電源層) にするか          LAYERS, PLANES
  * 取付穴                                                 MOUNTING_HOLES
  * 配線の前に置く銅ゾーン (電源のベタなど)                ZONES
  * 残し続ける禁止領域 (アンテナの下など)                  KEEPOUTS
  * 固定配線と固定ビア (ロックするのでルータは触らない)    TRACKS, VIAS
  * 面に落とすネットのファンアウト                          FANOUT
  * 配線の間だけの禁止領域: ZONES の輪郭、指定の領域、基板の縁
                                                           ROUTE_KEEPOUTS, EDGE_KEEPOUT
  * pre_hook(ctx)

post (セッションを取り込んだ後)
  * 配線用の禁止領域を外し、ルータの出力を掃除する
  * ベタ                                                   POURS
  * post_hook(ctx)
  * ステッチングビアと、ビアの届かない島への追加ビア        STITCH

どちらも何度流してもよい。前回足したものを先に消してから足し直す。消去は別プロセスで
行う (同じプロセスで基板を読み直すと SWIG のラッパが壊れる)。pre は前回の固定配線を
消すので、手で引いて固定したい線は KiCad 上でロックするのではなく TRACKS に書く。

設定ファイルは Python。書ける名前と意味は references/finish-config.md。どれも省略できる。
"""

import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pcbkit  # noqa: E402
from pcbkit import KEEP, POST, PRE, ROUTE, TAG  # noqa: E402


def load_config(path: str):
    spec = importlib.util.spec_from_file_location("finish_config", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    spec.loader.exec_module(mod)
    return mod


def cfg(mod, name, default=None):
    return getattr(mod, name, default)


def plane_nets(conf) -> set:
    nets = set(cfg(conf, "PLANES", {}).values())
    stitch = cfg(conf, "STITCH")
    if stitch:
        nets.add(stitch["net"])
    return nets


# --------------------------------------------------------------------------
def clear(pcb_path: str, stage: str, conf) -> int:
    """前回このスクリプトが足したものを消して保存する。消すものを全部集めてから消す。"""
    import pcbnew

    board = pcbnew.LoadBoard(pcb_path)
    doomed = []
    for z in board.Zones():
        name = z.GetZoneName() or ""
        if stage == "pre" and name.startswith(TAG + "-"):
            doomed.append(z)   # 前回のベタが残ると DSN に面として載り、ルータが詰まる
        elif stage == "post" and name.startswith((ROUTE, POST)):
            doomed.append(z)   # 配線用の禁止領域は外す (固定配線の端がかかって DRC に出る)
    doomed += pcbkit.own_mask_drawings(board)
    if stage == "pre":
        doomed += [t for t in board.GetTracks() if t.IsLocked()]
        doomed += [f for f in board.GetFootprints() if f.GetReference().startswith(pcbkit.HOLE_PREFIX)]
    else:
        stitch = cfg(conf, "STITCH")
        if stitch:
            doomed += pcbkit.loose_vias(board, {stitch["net"]})
        doomed += [d for d in pcbkit.router_junk(board, plane_nets(conf)) if d not in doomed]
    for item in doomed:
        board.Remove(item)
    board.Save(pcb_path)
    return len(doomed)


def pre(pcb_path: str, conf) -> list:
    import pcbnew

    board = pcbnew.LoadBoard(pcb_path)
    layers = cfg(conf, "LAYERS")
    planes = cfg(conf, "PLANES", {})
    notes = []
    if layers:
        notes.append(pcbkit.set_copper_layers(board, layers, list(planes)))
    elif planes:
        raise SystemExit("PLANES needs LAYERS")
    ctx = pcbkit.Ctx(board)   # 層を決めてから読む

    for layer, net in planes.items():
        ctx.zone(net, layer, ctx.inset(0.5), f"{PRE}plane-{layer}", 0, thermal=True)
    if planes:
        notes.append("planes: " + ", ".join(f"{n} on {l}" for l, n in planes.items()))

    holes = cfg(conf, "MOUNTING_HOLES")
    if holes:
        notes.append(ctx.mounting_holes(holes, cfg(conf, "HOLE_FOOTPRINT", "MountingHole_3.2mm_M3_DIN965")))

    zones = cfg(conf, "ZONES", [])
    for z in zones:
        layer = z.get("layer", "F.Cu")
        ctx.zone(z["net"], layer, z["points"], f"{PRE}{z.get('name', z['net'].lower())}-{layer}",
                 z.get("priority", 5), thermal=z.get("thermal", False))
    if zones:
        notes.append(f"{len(zones)} copper zone(s): " + ", ".join(sorted({z['net'] for z in zones})))

    for k in cfg(conf, "KEEPOUTS", []):
        ctx.keepout(k.get("layers", ctx.copper), k["points"], f"{KEEP}{k['name']}",
                    tracks=k.get("tracks", True), vias=k.get("vias", True), fills=k.get("fills", True))

    segs = 0
    for t in cfg(conf, "TRACKS", []):
        segs += ctx.track(t[0], t[1], t[2], t[3] if len(t) > 3 else "F.Cu")
    vias = cfg(conf, "VIAS", [])
    for v in vias:
        ctx.via(*v)
    if segs or vias:
        notes.append(f"{segs} locked track segment(s), {len(vias)} locked via(s)")

    hook = cfg(conf, "pre_hook")
    if hook:
        r = hook(ctx)
        if r:
            notes.append(r)

    fo = cfg(conf, "FANOUT")
    if fo:
        if fo["net"] not in planes.values():
            print(f"warning: FANOUT {fo['net']} has no plane in PLANES; the vias connect to nothing",
                  file=sys.stderr)
        placed, failed = pcbkit.fanout(ctx, fo["net"], fo.get("layers", ["F.Cu"]),
                                       clearance=fo.get("clearance", 0.25))
        notes.append(f"{fo['net']} fanout: {placed} pad(s) got a via"
                     + (f", no room for {failed}" if failed else ""))

    # Freerouting は信号層上のベタを他ネットの障害物として扱わない。配線の間だけ
    # 同じ輪郭の禁止領域で塞ぐ (references/routing.md)
    for z in zones:
        if z.get("block_routing", True):
            layer = z.get("layer", "F.Cu")
            ctx.keepout([layer], z["points"], f"{ROUTE}{z.get('name', z['net'].lower())}-{layer}")
    for k in cfg(conf, "ROUTE_KEEPOUTS", []):
        ctx.keepout(k.get("layers", ["F.Cu"]), k["points"], f"{ROUTE}{k['name']}")
    e = cfg(conf, "EDGE_KEEPOUT", 0.6)
    if e:
        l, t, r, b = ctx.edges
        frames = {"top": pcbkit.rect(l, t, r, t + e), "bottom": pcbkit.rect(l, b - e, r, b),
                  "left": pcbkit.rect(l, t, l + e, b), "right": pcbkit.rect(r - e, t, r, b)}
        for side, pts in frames.items():
            ctx.keepout(ctx.signal_layers(), pts, f"{ROUTE}edge-{side}")

    ctx.fill()
    board.Save(pcb_path)
    return notes


def post(pcb_path: str, conf) -> list:
    import pcbnew

    board = pcbnew.LoadBoard(pcb_path)
    ctx = pcbkit.Ctx(board)
    notes = []
    for p in cfg(conf, "POURS", []):
        layers = p.get("layers", [ctx.copper[0], ctx.copper[-1]])   # 省けば表裏
        ctx.pour(p["net"], layers, p.get("points"), p.get("name", ""), p.get("priority", 0))
        notes.append(f"{p['net']} pour on {', '.join(layers)}")
    hook = cfg(conf, "post_hook")
    if hook:
        r = hook(ctx)
        if r:
            notes.append(r)
    ctx.fill()
    stitch = cfg(conf, "STITCH")
    if stitch:
        n = pcbkit.stitch(ctx, stitch["net"], stitch.get("pitch", 3.0))
        ctx.fill()
        patched = pcbkit.patch_islands(ctx, stitch["net"])
        ctx.fill()
        notes.append(f"{n} {stitch['net']} stitching via(s), {patched} more for islands")
    board.Save(pcb_path)
    return notes


def main(pcb_path: str, stage: str, conf_path: str) -> int:
    conf = load_config(conf_path)
    if stage.startswith("clear-"):
        print(clear(pcb_path, stage[len("clear-"):], conf))
        return 0
    if stage == "pre":
        r = subprocess.run([sys.executable, os.path.join(HERE, "dedupe_uuids.py"), pcb_path],
                           capture_output=True, text=True)
        if r.returncode:
            print(r.stderr, file=sys.stderr)
            return r.returncode
    # 消去は別プロセスで行う。同じプロセスで基板を読み直すと、編集後の
    # SWIG ラッパが壊れたまま返ってきて何も呼べない
    r = subprocess.run([sys.executable, __file__, pcb_path, "clear-" + stage, conf_path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout + r.stderr, file=sys.stderr)
        return r.returncode
    removed = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "?"
    notes = pre(pcb_path, conf) if stage == "pre" else post(pcb_path, conf)
    print(f"stage {stage}: cleared {removed} previous item(s)")
    for n in notes:
        print(f"  {n}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[2] not in ("pre", "post", "clear-pre", "clear-post"):
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    pcbkit.exit_now(main(*sys.argv[1:]))
