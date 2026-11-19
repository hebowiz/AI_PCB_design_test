"""Board finishing that atopile cannot express, in two stages.

`pre` runs before autorouting and adds the module's antenna keep-out, so the
router never puts copper under the radio.

`post` runs after the session file is back and adds:

  * the ring electrode itself: a filled zone of radius RING_OUT_R on both
    copper layers, on the electrode net, with a rule area of radius RING_IN_R
    carving the middle out, and a ring-shaped opening in both solder masks so
    the copper is bare on each face,
  * a ground pour on the back of the electronics strip.

The electrode cannot live in the .kicad_mod: atopile re-serialises every
footprint it manages and drops custom pad primitives.

Both stages are idempotent - everything they add is tagged and removed first.

  $(scripts/kicad_python.sh) scripts/finish_board.py board.kicad_pcb pre|post
"""

import math
import os
import sys

import pcbnew

# the exposed copper runs from just clear of the centre hole out to RING_OUT_R.
# 0.5 mm of bare substrate is left at the hole: that is the usual minimum a
# fab will hold between copper and a routed edge.
RING_IN_R = 15.5
RING_OUT_R = 40.0
SEGMENTS = 192
TAG = "auto-pcb"
ANTENNA_MARGIN = 1.0   # keep-out grows this far around the radio's antenna end
STRIP_MARGIN = 1.0     # ground pour starts this far outside the electrode


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def circle_points(cx: float, cy: float, r: float) -> pcbnew.VECTOR_VECTOR2I:
    pts = pcbnew.VECTOR_VECTOR2I()
    for i in range(SEGMENTS):
        a = 2 * math.pi * i / SEGMENTS
        pts.append(pcbnew.VECTOR2I(mm(cx + r * math.cos(a)), mm(cy + r * math.sin(a))))
    return pts


def clear_previous(board: pcbnew.BOARD, stage: str, centre=None) -> int:
    """Remove what this stage previously added, so re-running is safe.

    Everything is collected before anything is removed: pcbnew invalidates its
    iterators as soon as the board is modified.
    """
    prefix = "%s-antenna" % TAG if stage == "pre" else "%s-" % TAG
    doomed = []
    for z in board.Zones():
        name = z.GetZoneName() or ""
        if not name.startswith(prefix):
            continue
        if stage == "post" and name.startswith("%s-antenna" % TAG):
            continue  # the keep-out belongs to the pre stage; leave it alone
        doomed.append(z)

    if stage == "post" and centre is not None:
        for d in board.GetDrawings():
            if d.GetLayer() not in (pcbnew.F_Mask, pcbnew.B_Mask):
                continue
            if d.GetShape() != pcbnew.SHAPE_T_CIRCLE:
                continue
            c = d.GetCenter()
            if (
                abs(pcbnew.ToMM(c.x) - centre[0]) < 0.01
                and abs(pcbnew.ToMM(c.y) - centre[1]) < 0.01
            ):
                doomed.append(d)

    for item in doomed:
        board.Remove(item)
    return len(doomed)


def rect_points(x0: float, y0: float, x1: float, y1: float) -> pcbnew.VECTOR_VECTOR2I:
    pts = pcbnew.VECTOR_VECTOR2I()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        pts.append(pcbnew.VECTOR2I(mm(x), mm(y)))
    return pts


def read_antenna_box(board: pcbnew.BOARD):
    """Where the radio's pad-free end is, in mm. Read before the board is edited."""
    module = next((f for f in board.GetFootprints() if f.GetReference() == "U2"), None)
    if module is None:
        return None
    bb = module.GetBoundingBox(False, False)
    pad_bottom = max(pcbnew.ToMM(p.GetPosition().y) for p in module.Pads())
    box = (
        pcbnew.ToMM(bb.GetLeft()),
        pcbnew.ToMM(bb.GetRight()),
        pad_bottom,
        pcbnew.ToMM(bb.GetBottom()),
    )
    return box if box[3] - box[2] >= 3.0 else None


def add_antenna_keepout(board: pcbnew.BOARD, box) -> str:
    """Forbid copper over the radio module's antenna end.

    The antenna is the part of the module outline that carries no pads, so it
    is found without hard-coding the module's dimensions.
    """
    if box is None:
        return "no pad-free module end found, no antenna keep-out added"
    left, right, pad_bottom, bottom = box

    ko = pcbnew.ZONE(board)
    ko.SetIsRuleArea(True)
    ko.SetDoNotAllowZoneFills(True)
    ko.SetDoNotAllowTracks(True)
    ko.SetDoNotAllowVias(True)
    layers = pcbnew.LSET()
    layers.AddLayer(pcbnew.F_Cu)
    layers.AddLayer(pcbnew.B_Cu)
    ko.SetLayerSet(layers)
    ko.SetZoneName(f"{TAG}-antenna-keepout")
    ko.AddPolygon(
        rect_points(
            left - ANTENNA_MARGIN,
            pad_bottom + ANTENNA_MARGIN,
            right + ANTENNA_MARGIN,
            bottom + ANTENNA_MARGIN,
        )
    )
    board.Add(ko)
    area = (right - left + 2 * ANTENNA_MARGIN) * (bottom - pad_bottom)
    return f"antenna keep-out added, {area:.0f} mm2 over both layers"


def add_electrode(board: pcbnew.BOARD, cx: float, cy: float, net):
    """Returns a note plus the two copper zones, so the caller can measure the fill."""
    zones = []
    for layer, side in ((pcbnew.F_Cu, "front"), (pcbnew.B_Cu, "back")):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNet(net)
        zone.SetZoneName(f"{TAG}-electrode-{side}")
        zone.AddPolygon(circle_points(cx, cy, RING_OUT_R))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        zone.SetIsFilled(False)
        zone.SetAssignedPriority(10)
        board.Add(zone)
        zones.append(zone)

    keepout = pcbnew.ZONE(board)
    keepout.SetIsRuleArea(True)
    keepout.SetDoNotAllowZoneFills(True)
    keepout.SetDoNotAllowTracks(False)
    keepout.SetDoNotAllowVias(False)
    ko_layers = pcbnew.LSET()
    ko_layers.AddLayer(pcbnew.F_Cu)
    ko_layers.AddLayer(pcbnew.B_Cu)
    keepout.SetLayerSet(ko_layers)
    keepout.SetZoneName(f"{TAG}-electrode-cutout")
    keepout.AddPolygon(circle_points(cx, cy, RING_IN_R))
    board.Add(keepout)

    # bare copper on both faces: a ring-shaped opening in the solder mask
    for layer in (pcbnew.F_Mask, pcbnew.B_Mask):
        ring = pcbnew.PCB_SHAPE(board)
        ring.SetShape(pcbnew.SHAPE_T_CIRCLE)
        ring.SetLayer(layer)
        ring.SetCenter(pcbnew.VECTOR2I(mm(cx), mm(cy)))
        ring.SetEnd(pcbnew.VECTOR2I(mm(cx + (RING_IN_R + RING_OUT_R) / 2), mm(cy)))
        ring.SetWidth(mm(RING_OUT_R - RING_IN_R))
        ring.SetFilled(False)
        board.Add(ring)
    return "electrode zones and mask openings added", zones


def add_ground_pour(board: pcbnew.BOARD, cy: float, edges, gnd, below_electrode: bool) -> str:
    """Pour ground. Both faces normally; only the back when an electrode owns the front.

    One face is not enough on its own: the router leaves ground stubs on the
    other layer with no via to reach the plane, and DRC calls them unconnected.
    """
    if gnd is None:
        return "no ground net named `lv`, no pour added"
    left, right, board_top, bottom = edges
    top = cy + RING_OUT_R + STRIP_MARGIN if below_electrode else board_top
    layers = [pcbnew.B_Cu] if below_electrode else [pcbnew.F_Cu, pcbnew.B_Cu]

    for layer in layers:
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNet(gnd)
        zone.SetZoneName(f"{TAG}-ground-pour-{pcbnew.LayerName(layer)}")
        zone.AddPolygon(rect_points(left, top, right, bottom))
        zone.SetIsFilled(False)
        zone.SetAssignedPriority(1)
        board.Add(zone)
    names = ", ".join(pcbnew.LayerName(l) for l in layers)
    return f"ground pour added on {names}, y {top:.0f}..{bottom:.0f} mm"


def main(pcb_path: str, stage: str) -> int:
    board = pcbnew.LoadBoard(pcb_path)

    # the ring electrode is optional: a board without one just gets the pour
    electrode = next((f for f in board.GetFootprints() if f.GetReference() == "E1"), None)
    cx = cy = 0.0
    net = None
    if electrode is not None:
        pos = electrode.GetPosition()
        cx, cy = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
        net = next((p.GetNet() for p in electrode.Pads() if p.GetNetname()), None)
        if net is None:
            print("E1 has no net; run `ato build` first", file=sys.stderr)
            return 1

    # everything the new zones need is read before the board is touched:
    # pcbnew hands back dead wrappers once items have been added or removed.
    antenna_box = read_antenna_box(board) if stage == "pre" else None
    eb = board.GetBoardEdgesBoundingBox()
    edges = (
        pcbnew.ToMM(eb.GetLeft()),
        pcbnew.ToMM(eb.GetRight()),
        pcbnew.ToMM(eb.GetTop()),
        pcbnew.ToMM(eb.GetBottom()),
    )
    gnd = board.FindNet("lv")

    removed = clear_previous(board, stage, (cx, cy))
    notes = []
    if stage == "pre":
        notes.append(add_antenna_keepout(board, antenna_box))
    else:
        zones = []
        if electrode is not None:
            note, zones = add_electrode(board, cx, cy, net)
            notes.append(note)
        else:
            notes.append("no E1 on the board, no electrode copper")
        notes.append(add_ground_pour(board, cy, edges, gnd, electrode is not None))
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        if zones:
            area = sum(z.GetFilledArea() for z in zones)
            notes.append(
                f"electrode copper r{RING_IN_R}..{RING_OUT_R}mm filled on both faces, "
                f"{pcbnew.ToMM(pcbnew.ToMM(area)):.0f} mm2"
            )

    board.Save(pcb_path)
    print(f"stage {stage}: cleared {removed} previous item(s)")
    for n in notes:
        print(f"  {n}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in ("pre", "post"):
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    code = main(sys.argv[1], sys.argv[2])
    # pcbnew's SWIG bindings crash while tearing the board down at interpreter
    # exit, long after the file is written. Leave without running that teardown.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
