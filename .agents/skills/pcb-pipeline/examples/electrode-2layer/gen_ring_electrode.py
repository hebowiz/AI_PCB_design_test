"""Generate the ring-electrode part: a .kicad_mod plus a matching one-pin .kicad_sym.

The electrode is a copper annulus exposed on both sides, stitched with vias, and it
also carries the board outline (outer rounded rectangle + centre hole). Keeping the
outline inside the footprint means `ato build` can never drop it.

  python3 scripts/gen_ring_electrode.py board/parts/RingElectrode
"""

import math
import pathlib
import sys

# --- geometry, mm ----------------------------------------------------------
HOLE_R = 15.0        # centre hole, diameter 30
RING_IN_R = 15.5     # annulus inner radius: 0.5mm clear of the centre hole
RING_OUT_R = 40.0    # annulus outer radius
BOARD_X = 45.0       # board spans -BOARD_X .. +BOARD_X
BOARD_TOP = -45.0    # ring centre is the origin
BOARD_BOTTOM = 70.0  # electronics strip lives between the ring and this edge
CORNER_R = 3.0
VIA_COUNT = 24
ANCHOR_R = 38.0   # anchor pad sits inside the annulus, nearest the electronics
VIA_DRILL = 0.4
VIA_PAD = 0.8

RING_MID_R = (RING_IN_R + RING_OUT_R) / 2
RING_WIDTH = RING_OUT_R - RING_IN_R


def rounded_rect_edges(x0: float, y0: float, x1: float, y1: float, r: float) -> list[str]:
    """Edge.Cuts lines + arcs for a rounded rectangle."""
    out = []
    seg = lambda ax, ay, bx, by: (
        f'  (fp_line (start {ax:.3f} {ay:.3f}) (end {bx:.3f} {by:.3f})'
        f' (stroke (width 0.1) (type solid)) (layer "Edge.Cuts"))'
    )
    out += [
        seg(x0 + r, y0, x1 - r, y0),
        seg(x1, y0 + r, x1, y1 - r),
        seg(x1 - r, y1, x0 + r, y1),
        seg(x0, y1 - r, x0, y0 + r),
    ]
    k = r * (1 - math.sqrt(0.5))
    corners = [
        ((x0 + r, y0), (x0 + k, y0 + k), (x0, y0 + r)),
        ((x1, y0 + r), (x1 - k, y0 + k), (x1 - r, y0)),
        ((x1 - r, y1), (x1 - k, y1 - k), (x1, y1 - r)),
        ((x0, y1 - r), (x0 + k, y1 - k), (x0 + r, y1)),
    ]
    for (sx, sy), (mx, my), (ex, ey) in corners:
        out.append(
            f'  (fp_arc (start {sx:.3f} {sy:.3f}) (mid {mx:.3f} {my:.3f})'
            f' (end {ex:.3f} {ey:.3f}) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts"))'
        )
    return out


def footprint() -> str:
    body = [
        '(footprint "RingElectrode"',
        "  (version 20241229)",
        '  (generator "auto-pcb")',
        "  (layer \"F.Cu\")",
        "  (attr exclude_from_pos_files exclude_from_bom)",
        '  (property "Reference" "E1" (at 0 -20 0) (layer "F.SilkS")'
        " (effects (font (size 1.5 1.5) (thickness 0.25))))",
        '  (property "Value" "RingElectrode" (at 0 20 0) (layer "F.Fab")'
        " (effects (font (size 1.5 1.5) (thickness 0.25))))",
    ]

    # anchor pad: atopile re-serialises footprints and drops custom pad
    # primitives, so the annulus itself is built as a copper zone after the
    # build (scripts/add_electrode_copper.py). This pad only gives the net a
    # foothold on the ring, placed on the side facing the electronics.
    body += [
        f'  (pad "1" smd circle (at 0 {ANCHOR_R:.3f}) (size 2 2)'
        ' (layers "F.Cu" "F.Mask"))',
        f'  (pad "1" smd circle (at 0 {ANCHOR_R:.3f}) (size 2 2)'
        ' (layers "B.Cu" "B.Mask"))',
    ]

    # stitching vias tie the two faces together
    for i in range(VIA_COUNT):
        a = 2 * math.pi * i / VIA_COUNT
        x, y = RING_MID_R * math.cos(a), RING_MID_R * math.sin(a)
        body.append(
            f'  (pad "1" thru_hole circle (at {x:.3f} {y:.3f})'
            f' (size {VIA_PAD} {VIA_PAD}) (drill {VIA_DRILL}) (layers "*.Cu"))'
        )

    # board outline + centre hole
    body += rounded_rect_edges(-BOARD_X, BOARD_TOP, BOARD_X, BOARD_BOTTOM, CORNER_R)
    body.append(
        f'  (fp_circle (center 0 0) (end {HOLE_R:.3f} 0) (stroke (width 0.1) (type solid))'
        ' (fill none) (layer "Edge.Cuts"))'
    )
    body.append(")")
    return "\n".join(body) + "\n"


def symbol() -> str:
    return """(kicad_symbol_lib
	(version 20241229)
	(generator "auto-pcb")
	(symbol "RingElectrode"
		(property "Reference" "E" (id 0) (at 0 5.08 0)
			(effects (font (size 1.27 1.27))))
		(property "Value" "RingElectrode" (id 1) (at 0 -5.08 0)
			(effects (font (size 1.27 1.27))))
		(property "Footprint" "RingElectrode:RingElectrode" (id 2) (at 0 -7.62 0)
			(effects (font (size 1.27 1.27)) hide))
		(property "Datasheet" "" (id 3) (at 0 -10.16 0)
			(effects (font (size 1.27 1.27)) hide))
		(in_bom no)
		(on_board yes)
		(symbol "RingElectrode_0_1"
			(circle (center 0 0) (radius 2.54)
				(stroke (width 0.254) (type default))
				(fill (type none)))
			(circle (center 0 0) (radius 1.27)
				(stroke (width 0.254) (type default))
				(fill (type none)))
		)
		(symbol "RingElectrode_1_1"
			(pin passive line (at 7.62 0 180) (length 5.08)
				(name "E" (effects (font (size 1.27 1.27))))
				(number "1" (effects (font (size 1.27 1.27))))
			)
		)
	)
)
"""


ATO = """import has_designator_prefix
import has_part_removed
import is_atomic_part

component RingElectrode:
    \"\"\"両面に露出した導体リング。穴の縁から 0.5mm を残し、外半径 40mm まで。

    中央の直径 30mm の穴と基板外形もこのフットプリントが持つ。
    外形をフットプリント側に置くことで ato build で消えない。
    \"\"\"

    trait is_atomic_part<manufacturer="-", partnumber="RING-ELECTRODE", footprint="RingElectrode.kicad_mod", symbol="RingElectrode.kicad_sym">
    trait has_part_removed
    trait has_designator_prefix<prefix="E">

    signal E ~ pin 1
"""


def main(outdir: str) -> int:
    d = pathlib.Path(outdir)
    d.mkdir(parents=True, exist_ok=True)
    (d / "RingElectrode.kicad_mod").write_text(footprint())
    (d / "RingElectrode.kicad_sym").write_text(symbol())
    (d / "RingElectrode.ato").write_text(ATO)
    print(f"wrote {d}/RingElectrode.{{kicad_mod,kicad_sym,ato}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "board/parts/RingElectrode"))
