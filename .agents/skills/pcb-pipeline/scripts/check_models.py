"""EasyEDA 由来のフットプリントの壊れ方を一覧にする。

`ato create part` や部品選定で取り込んだフットプリントには、次の壊れ方がある。
どちらも DRC では見つからない。

  * 3D モデルのオフセットが 0 でない。表示だけ部品がずれ、3D レンダで別の部品の
    下に潜って見える。実例: FOJAN FRC1206J2R2 TS (C2907445) の 1206 が (-2.39, 0.89)
  * 表面実装部品なのに実装属性が through_hole。`kicad-cli pcb export pos --smd-only`
    で実装座標から落ちる。実例: HRK GVZ1H107M0810CNVC (100uF 電解), 上の FOJAN

フットプリントを手で直しても `ato build` で取り込み直すと元に戻る。別の LCSC 番号の
部品に替え、`make fresh` からやり直す。端子台などは 0.3mm 程度のずれが元から付いて
いることがあり、それは実害が無い。

  $(scripts/kicad_python.sh) scripts/check_models.py board.kicad_pcb [min_mm]

問題があれば一覧を出して終了コード 1。
"""

import sys

import pcbnew


def main(path: str, min_mm: float) -> int:
    board = pcbnew.LoadBoard(path)
    bad = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        name = fp.GetFPID().GetLibItemName()
        for m in fp.Models():
            dx, dy = m.m_Offset.x, m.m_Offset.y
            if max(abs(dx), abs(dy)) > min_mm:
                print(f"{ref}\t{name}\t3D model offset ({dx:g}, {dy:g}) mm")
                bad += 1
        pads = list(fp.Pads())
        smd_only = pads and all(p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for p in pads)
        if smd_only and fp.GetAttributes() & pcbnew.FP_THROUGH_HOLE:
            print(f"{ref}\t{name}\tSMD pads but footprint attribute is through_hole")
            bad += 1
    print(f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 0.5))
