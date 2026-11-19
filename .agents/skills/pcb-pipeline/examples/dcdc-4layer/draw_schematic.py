"""DC-DC 基板の回路図。配置はここで手で決め、正しさは scripts/schematic.py が照合する。

  python3 draw_schematic.py board/layouts/default/default.kicad_pcb docs/netlist.md docs/schematic.svg

スキルの scripts/ を import できるように、SKILL_SCRIPTS か相対パスで探す。
"""

import os
import sys

sys.path.insert(0, os.environ.get("SKILL_SCRIPTS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../scripts")))

from schematic import (  # noqa: E402
    MUTED, Sheet, decap, designators, flag, gnd, ic, label, netlist, nmos, npn, opamp, testpoint, two,
    write,
)

# 部品番号から引いた値では読みにくいものだけ、ここで言い換える
VALUE_NOTE = {
    "shunt": "5mΩ 3W",
    "c_out": "470µF 35V",
    "c_in_bulk": "100µF 50V",
    "l": "47µH 8.7A",
    "j_in": "入力端子",
    "j_out": "出力端子",
    "j_mcu": "マイコン接続 2x5",
    "d": "SS10P6 60V 10A",
    "reg12": "L78L12",
    "reg33": "AMS1117-3.3",
    "q": "NTMFS5C670NL 60V",
    "q_ramp": "MMBT3904",
    "led": "緑",
}


# --------------------------------------------------------------------------
# the drawing
# --------------------------------------------------------------------------
def draw(refs: dict, values: dict) -> Sheet:
    s = Sheet(2820, 2140, refs, values, VALUE_NOTE)

    s.text(40, 46, "DGC 実験用 非同期降圧コンバータ", 24, weight="bold")
    s.text(40, 72, "board/main.ato から起こした回路図。接続は docs/netlist.md と 1 ピンずつ一致を検証済み。"
           "同じ名前の赤ラベルは同じネット。", 13, color=MUTED)
    s.text(40, 94, "E = 20V → Vo = 15V, 連続 5A, 約 110kHz。"
           "MODE = L: UCC28C43 のピーク電流モード / MODE = H: 外部マイコンの GATE_EXT を直接 (DGC)", 13, color=MUTED)

    power_stage(s)
    driver(s)
    current_sense(s)
    controller(s)
    gate_logic(s)
    overcurrent(s)
    monitors(s)
    aux_supply(s)
    header_and_testpoints(s)
    decoupling(s)
    return s


def power_stage(s: Sheet) -> None:
    s.block(30, 110, 2120, 440, "パワー段")
    rail, g = 220, 330

    j = ic(s, "j_in", 50, 190, 60, 140,
           right=[("+", 30, "1", "VIN"), ("−", 110, "2", "GND")])
    s.wire(j["+"], (1000, rail))
    s.wire(j["−"], (150, 300), (150, g))
    gnd(s, 150, g)
    label(s, 170, rail - 12, "VIN", "middle")

    two(s, "TVS", "tvs", (200, g), (200, rail), "GND", "VIN", pa="2", pb="1")
    gnd(s, 200, g)
    s.dot(200, rail)
    for i, (addr, kind) in enumerate((("c_in_bulk", "CP"), ("c_in1", "C"), ("c_in2", "C"),
                                      ("c_in3", "C"), ("c_in_hf1", "C"), ("c_in_hf2", "C"))):
        x = 290 + i * 100
        two(s, kind, addr, (x, rail), (x, g), "VIN", "GND")
        gnd(s, x, g)
        s.dot(x, rail)
    with s.shift(100):
        _power_stage_rest(s, rail)


def _power_stage_rest(s: Sheet, rail: int) -> None:

    # VIN_S: 小電流の枝を取り出す 0Ω タップ
    two(s, "R", "r_vin_tap", (770, rail), (770, 130 + 22), "VIN", "VIN_S")
    s.dot(770, rail)
    flag(s, 770, 152, "VIN_S")

    q = nmos(s, "q", 900, 290)
    s.pin("q", "5", "VIN")
    s.pin("q", "4", "GATE")
    s.pin("q", "1,2,3", "SW")
    node_g = (815, 290)
    s.wire(q["g"], node_g)
    s.dot(*node_g)
    label(s, node_g[0], node_g[1] - 18, "GATE", "middle")
    s.wire(node_g, (815, 272))
    two(s, "R", "r_gs", node_g, (815, 400), "GATE", "SW", side="l")
    sw = 400
    s.wire((815, sw), (900, sw), q["s"])
    s.dot(900, sw)

    # SW ノード
    s.wire((900, sw), (1160, sw))
    label(s, 1150, sw - 10, "SW", "middle")
    two(s, "D", "d", (980, 510), (980, sw), "GND", "SW", pa="1,2", pb="3", side="l")
    gnd(s, 980, 510)
    s.dot(980, sw)
    testpoint(s, "tp_sw", 1040, sw, "SW")
    s.dot(1040, sw)
    two(s, "R", "r_snub", (1100, sw), (1100, 450), "SW", "SNUB")
    s.dot(1100, sw)
    two(s, "C", "c_snub", (1100, 450), (1100, 520), "SNUB", "GND")
    s.dot(1100, 450)
    s.wire((1100, 450), (1070, 450))
    label(s, 1070, 450, "SNUB", "end")
    gnd(s, 1100, 520)

    two(s, "L", "l", (1160, sw), (1300, sw), "SW", "IL_P")
    s.wire((1300, sw), (1340, sw))
    s.dot(1340, sw)
    label(s, 1330, sw - 10, "IL_P", "middle")
    two(s, "R", "shunt", (1340, sw), (1480, sw), "IL_P", "VOUT")
    s.wire((1480, sw), (1920, sw))
    s.dot(1520, sw)
    label(s, 1545, sw - 10, "VOUT", "middle")

    two(s, "C", "c_out_hf", (1590, sw), (1590, 490), "VOUT", "GND")
    two(s, "CP", "c_out", (1700, sw), (1700, 490), "VOUT", "GND")
    for x in (1590, 1700):
        gnd(s, x, 490)
        s.dot(x, sw)
    two(s, "R", "r_vout_tap", (1780, sw), (1780, 262), "VOUT", "VOUT_S", side="l")
    s.dot(1780, sw)
    flag(s, 1780, 262, "VOUT_S")
    testpoint(s, "tp_vout", 1850, sw, "VOUT")
    s.dot(1850, sw)

    j = ic(s, "j_out", 1940, 370, 60, 140,
           left=[("+", 30, "1", "VOUT"), ("−", 110, "2", "GND")])
    s.wire(j["−"], (1900, 480), (1900, 500))
    gnd(s, 1900, 500)

    s.text(1180, 150, "iL は L の出力側の 5mΩ で測る (同相電圧 = vo で静か)", 12, color=MUTED)
    s.text(1180, 168, "0Ω タップ R (VIN_S, VOUT_S) で小電流の取り出し点を固定", 12, color=MUTED)


def driver(s: Sheet) -> None:
    s.block(30, 570, 1000, 400, "ハイサイドドライバ (LTC7001, チャージポンプ内蔵)")
    x, y, w, h = 460, 650, 200, 240
    p = ic(s, "drv", x, y, w, h,
           top=[("VCC", 60, "1", "VCC12")],
           left=[("VCCUV", 30, "2", None), ("INP", 80, "4", "INP"), ("OVLO", 140, "5", "OVLO")],
           right=[("BST", 30, "9", "BST"), ("TS", 80, "8", "SW"),
                  ("TGUP", 135, "7", "TGUP"), ("TGDN", 215, "6", "TGDN")],
           bottom=[("GND", 60, "3", "GND"), ("EP", 120, "11", "GND"), ("NC", 170, "10", None)])
    s.wire(p["VCC"], (520, 615))
    flag(s, 520, 615, "VCC12")
    s.text(428, 684, "開放 (UVLO 7V)", 11, "end", MUTED)
    s.wire(p["INP"], (400, p["INP"][1]))
    label(s, 400, p["INP"][1], "INP", "end")
    for q in ("GND", "EP"):
        gnd(s, *p[q])

    # OVLO: 1.21V x 230k / 10k = 27.8V で停止
    yo = p["OVLO"][1]
    s.wire(p["OVLO"], (300, yo))
    two(s, "R", "r_ov_top", (300, 690), (300, yo), "VIN_S", "OVLO", side="l")
    flag(s, 300, 690, "VIN_S")
    two(s, "R", "r_ov_bot", (300, yo), (300, 900), "OVLO", "GND", side="l")
    gnd(s, 300, 900)
    two(s, "C", "c_ov", (370, yo), (370, 900), "OVLO", "GND")
    gnd(s, 370, 900)
    s.dot(300, yo)
    s.dot(370, yo)
    s.text(90, 950, "OVLO: VIN > 27.8V で停止", 12, color=MUTED)

    # ブートストラップ
    bx = 760
    s.wire(p["BST"], (bx, p["BST"][1]))
    two(s, "D", "d_bst", (bx, 610), (bx, p["BST"][1]), "VCC12", "BST", pa="2", pb="1")
    flag(s, bx, 610, "VCC12")
    two(s, "C", "c_bst", (bx, p["BST"][1]), (bx, p["TS"][1]), "BST", "SW")
    s.dot(bx, p["BST"][1])
    s.wire(p["TS"], (860, p["TS"][1]))
    s.dot(bx, p["TS"][1])
    label(s, 860, p["TS"][1], "SW")

    # ゲート抵抗: オン 4.7Ω / オフ 1Ω
    gx = 900
    two(s, "R", "r_gon", p["TGUP"], (gx, p["TGUP"][1]), "TGUP", "GATE")
    two(s, "R", "r_goff", p["TGDN"], (gx, p["TGDN"][1]), "TGDN", "GATE")
    ym = (p["TGUP"][1] + p["TGDN"][1]) // 2
    s.wire((gx, p["TGUP"][1]), (gx, p["TGDN"][1]))
    s.wire((gx, ym), (930, ym))
    s.dot(gx, ym)
    label(s, 930, ym, "GATE")


def current_sense(s: Sheet) -> None:
    with s.shift(100):
        _current_sense(s)


def _current_sense(s: Sheet) -> None:
    s.block(1060, 570, 560, 400, "電流検出 (5mΩ × 50V/V = 0.25V/A)")
    # シャントの両端から下ろす (パワー段の IL_P / VOUT ノードの続き)
    xp, xn, top, ya = 1340, 1520, 400, 620
    s.wire((xp, top), (xp, 440))
    s.wire((xn, top), (xn, 440))
    two(s, "R", "r_isp", (xp, 440), (xp, ya), "IL_P", "ISNS_P", side="l")
    two(s, "R", "r_isn", (xn, 440), (xn, ya), "VOUT", "ISNS_N")
    two(s, "C", "c_isd", (xp, ya), (xn, ya), "ISNS_P", "ISNS_N")
    s.dot(xp, ya)
    s.dot(xn, ya)
    x, y, w = 1300, 700, 260
    p = ic(s, "isns", x, y, w, 150, title="INA241A3 (50V/V)",
           top=[("IN+", xp - x, "8", "ISNS_P"), ("IN−", xn - x, "1", "ISNS_N")],
           left=[("VS", 50, "6", "3V3")],
           right=[("OUT", 50, "5", "I_MON")],
           bottom=[("GND", 40, "2", "GND"), ("NC", 100, "4", "GND"),
                   ("REF2", 160, "3", "GND"), ("REF1", 220, "7", "GND")])
    s.wire((xp, ya), p["IN+"])
    s.wire((xn, ya), p["IN−"])
    s.wire(p["VS"], (1262, 750), (1262, 735))
    flag(s, 1262, 735, "3V3")
    s.wire(p["OUT"], (1590, 750))
    label(s, 1590, 750, "I_MON")
    for lbl in ("GND", "NC", "REF2", "REF1"):
        gnd(s, *p[lbl])


def controller(s: Sheet) -> None:
    with s.shift(100):
        _controller(s)


def _controller(s: Sheet) -> None:
    s.block(1650, 570, 1040, 780, "コントローラ UCC28C43 (ピーク電流モード)")
    x, y, w, h = 2160, 660, 180, 240
    p = ic(s, "ctl", x, y, w, h,
           left=[("COMP", 30, "1", "COMP"), ("FB", 90, "2", "FB"),
                 ("CS", 160, "3", "CS"), ("RT/CT", 210, "4", "RT_CT")],
           right=[("VREF", 30, "8", "VREF"), ("VDD", 90, "7", "VCC12"), ("OUT", 160, "6", "CTL_OUT")],
           bottom=[("GND", 90, "5", "GND")])
    gnd(s, *p["GND"])

    # 位相補償 Type II: COMP と FB の間に R1+C6 と C5
    xc, xf = 2060, 1860
    yc, yf = p["COMP"][1], p["FB"][1]
    s.wire(p["COMP"], (xc, yc), (xc, 630))
    s.wire(p["FB"], (xf, yf), (xf, 630))
    two(s, "C", "c_comp_hf", (xc, 630), (xf, 630), "COMP", "FB")
    s.wire((xc, 630), (xc, 700))
    s.wire((xf, 630), (xf, 700))
    s.dot(xc, 630)
    s.dot(xf, 630)
    two(s, "R", "r_comp", (xc, 700), (1960, 700), "COMP", "COMP_RC")
    two(s, "C", "c_comp", (1960, 700), (xf, 700), "COMP_RC", "FB")
    s.dot(xc, yc)
    s.dot(xf, 700)
    label(s, 2100, yc, "COMP", "middle")

    # FB 分圧: 2.5V x (1 + 10k/2k) = 15.0V
    xd = 1760
    s.wire((xf, yf), (xd, yf))
    s.dot(xf, yf)
    two(s, "R", "r_fb_top", (xd, 640), (xd, yf), "VOUT_S", "FB", side="l")
    flag(s, xd, 640, "VOUT_S")
    two(s, "R", "r_fb_bot", (xd, yf), (xd, 850), "FB", "GND", side="l")
    gnd(s, xd, 850)
    s.dot(xd, yf)
    label(s, 1810, yf, "FB", "middle")
    s.text(1680, 940, f"Vo = 2.5V × (1 + {s.ref('r_fb_top')}/{s.ref('r_fb_bot')}) = 15.0V", 12, color=MUTED)

    for lbl, net in (("CS", "CS"), ("RT/CT", "RT_CT")):
        s.wire(p[lbl], (2080, p[lbl][1]))
        label(s, 2080, p[lbl][1], net, "end")
    s.wire(p["VREF"], (2420, p["VREF"][1]))
    label(s, 2420, p["VREF"][1], "VREF")
    s.wire(p["VDD"], (2420, p["VDD"][1]))
    label(s, 2420, p["VDD"][1], "VCC12")

    # OUT (0-12V) を 3.3V ロジックへ分圧
    yo = p["OUT"][1]
    two(s, "R", "r_od_top", p["OUT"], (2500, yo), "CTL_OUT", "PWM_IC")
    s.wire((2500, yo), (2580, yo))
    two(s, "R", "r_od_bot", (2540, yo), (2540, 910), "PWM_IC", "GND")
    gnd(s, 2540, 910)
    s.dot(2540, yo)
    label(s, 2580, yo, "PWM_IC")

    # 発振 約 110kHz とスロープ補償
    yb = 1000
    xr = 1760
    two(s, "R", "r_rt", (xr, yb), (xr, 1120), "VREF", "RT_CT", side="l")
    flag(s, xr, yb, "VREF")
    two(s, "C", "c_ct", (xr, 1120), (xr, 1220), "RT_CT", "GND", side="l")
    gnd(s, xr, 1220)
    s.dot(xr, 1120)
    q = npn(s, "q_ramp", 1900, 1120)
    s.pin("q_ramp", "1", "RT_CT")
    s.pin("q_ramp", "3", "VREF")
    s.pin("q_ramp", "2", "RAMP")
    s.wire((xr, 1120), q["b"])
    label(s, 1820, 1120, "RT_CT", "middle")
    s.wire(q["c"], (q["c"][0], 1030))
    flag(s, q["c"][0], 1030, "VREF")
    xe = q["e"][0]
    s.wire(q["e"], (xe, 1210))
    two(s, "R", "r_ramp_e", (xe, 1210), (xe, 1300), "RAMP", "GND", side="l")
    gnd(s, xe, 1300)
    s.dot(xe, 1210)
    label(s, xe - 4, 1200, "RAMP", "end")

    xs = 2100
    two(s, "R", "r_ramp", (xe, 1210), (xs, 1210), "RAMP", "CS")
    two(s, "R", "r_cs_a", (xs, 1080), (xs, 1210), "I_MON", "CS")
    s.wire((xs, 1080), (xs, 1060))
    label(s, xs, 1060, "I_MON", "middle")
    two(s, "R", "r_cs_b", (xs, 1210), (xs, 1300), "CS", "GND")
    gnd(s, xs, 1300)
    s.wire((xs, 1210), (2220, 1210))
    two(s, "C", "c_cs", (2180, 1210), (2180, 1300), "CS", "GND")
    gnd(s, 2180, 1300)
    s.dot(xs, 1210)
    s.dot(2180, 1210)
    label(s, 2220, 1210, "CS")
    s.text(2300, 1040, "CS = 0.355 × I_MON + 0.113 × RAMP", 12, color=MUTED)
    s.text(2300, 1058, "iL 0.089V/A, CS 上限 1V で約 9A", 12, color=MUTED)
    s.text(2300, 1076, "Q1 で RT/CT の鋸波を取り出し", 12, color=MUTED)
    s.text(2300, 1094, "スロープ補償 (D > 0.5 対策)", 12, color=MUTED)


def gate_logic(s: Sheet) -> None:
    s.block(30, 1000, 1000, 455, "ゲート信号の選択: INP = (MODE ? GATE_EXT : PWM_IC) AND OC_OK")
    x, y = 560, 1070
    m = ic(s, "mux", x, y, 140, 150, title="74LVC1G157 (2:1 MUX)", title_at=(620, 1290, "start"),
           left=[("I0", 35, "3", "PWM_IC"), ("I1", 110, "1", "GATE_EXT_F")],
           right=[("Y", 75, "4", "GATE_SEL")],
           top=[("VCC", 70, "5", "3V3")],
           bottom=[("S", 40, "6", "MODE_F"), ("GND", 110, "2", "GND")])
    s.wire(m["I0"], (480, m["I0"][1]))
    label(s, 480, m["I0"][1], "PWM_IC", "end")
    s.wire(m["VCC"], (630, 1042))
    flag(s, 630, 1042, "3V3")
    gnd(s, *m["GND"])

    yi = m["I1"][1]
    s.wire((140, yi), (180, yi))
    label(s, 140, yi, "GATE_EXT", "end")
    two(s, "R", "r_gext", (180, yi), (340, yi), "GATE_EXT", "GATE_EXT_F")
    s.wire((340, yi), m["I1"])
    two(s, "R", "r_gext_pd", (400, yi), (400, 1270), "GATE_EXT_F", "GND", side="l")
    gnd(s, 400, 1270)
    s.dot(400, yi)
    label(s, 470, yi, "GATE_EXT_F", "middle")

    ym = 1355
    s.wire(m["S"], (600, ym), (480, ym))
    two(s, "R", "r_mode_pd", (480, ym), (480, 1412), "MODE_F", "GND")
    gnd(s, 480, 1412)
    s.dot(480, ym)
    two(s, "R", "r_mode", (300, ym), (480, ym), "MODE", "MODE_F")
    s.wire((300, ym), (260, ym))
    label(s, 260, ym, "MODE", "end")
    s.text(90, 1400, "GATE_EXT, MODE は未接続なら L", 12, color=MUTED)
    s.text(90, 1418, "(IC モード, 外部ゲート OFF)", 12, color=MUTED)

    a = ic(s, "gand", 830, 1090, 110, 110, title="74LVC1G08 (AND)",
           left=[("A", 30, "2", "GATE_SEL"), ("B", 80, "1", "OC_OK")],
           right=[("Y", 55, "4", "INP")],
           top=[("VCC", 55, "5", "3V3")],
           bottom=[("GND", 55, "3", "GND")])
    s.wire(m["Y"], (770, m["Y"][1]), (770, a["A"][1]), a["A"])
    label(s, 745, m["Y"][1] - 26, "GATE_SEL", "middle")
    s.wire(a["B"], (780, a["B"][1]))
    label(s, 780, a["B"][1], "OC_OK", "end")
    s.wire(a["Y"], (990, a["Y"][1]))
    label(s, 990, a["Y"][1] - 10, "INP", "middle")
    s.wire(a["VCC"], (885, 1062))
    flag(s, 885, 1062, "3V3")
    gnd(s, *a["GND"])


def overcurrent(s: Sheet) -> None:
    s.block(1060, 1000, 560, 440, "過電流遮断 (I_MON > 2.72V ≒ 11A で OC_OK = L)")
    c = opamp(s, "cmp", 1240, 1250, title="TLV3201")
    s.pin("cmp", "3", "OCP_TH")
    s.pin("cmp", "4", "I_MON")
    s.pin("cmp", "1", "OC_OK")
    s.pin("cmp", "5", "3V3")
    s.pin("cmp", "2", "GND")
    s.wire(c["vpos"], (c["vpos"][0], 1160))
    flag(s, c["vpos"][0], 1160, "3V3")
    s.wire(c["vneg"], (c["vneg"][0], 1320))
    gnd(s, c["vneg"][0], 1320)

    yp = c["plus"][1]
    s.wire(c["plus"], (1100, yp))
    two(s, "R", "r_th_top", (1160, 1110), (1160, yp), "3V3", "OCP_TH", side="l")
    flag(s, 1160, 1110, "3V3")
    s.dot(1160, yp)
    two(s, "R", "r_th_bot", (1100, yp), (1100, 1330), "OCP_TH", "GND", side="l")
    gnd(s, 1100, 1330)
    label(s, 1200, yp, "OCP_TH", "middle")

    ym = c["minus"][1]
    s.wire(c["minus"], (1200, ym), (1200, 1350))
    label(s, 1200, 1368, "I_MON", "middle")

    xo = 1400
    s.wire(c["out"], (1480, c["out"][1]))
    s.dot(xo, c["out"][1])
    label(s, 1480, c["out"][1], "OC_OK")
    # ヒステリシス 約 0.9A
    s.wire((xo, c["out"][1]), (xo, 1400))
    two(s, "R", "r_hys", (xo, 1400), (1160, 1400), "OC_OK", "OCP_TH")
    s.wire((1160, 1400), (1140, 1400), (1140, yp))
    s.dot(1140, yp)


def monitors(s: Sheet) -> None:
    s.block(30, 1470, 1700, 400, "マイコンへのモニタ出力 (すべて 0-3.3V)")
    top = 1580
    for x0, src, rt, rb, cd, div, pad_in, pad_neg, pad_out, rout, fbnet, cout, mon, unit, note in (
        (100, "VOUT_S", "r_vo_top", "r_vo_bot", "c_vo_div", "VO_DIV", "3", "2", "1",
         "r_vo_out", "IN1neg", "c_vo_out", "VO_MON", "A", "VO_MON = vo × 0.1304"),
        (720, "VIN_S", "r_vin_top", "r_vin_bot", "c_vin_div", "VIN_DIV", "5", "6", "7",
         "r_vin_out", "IN2neg", "c_vin_out", "VIN_MON", "B", "VIN_MON = vin × 0.1304"),
    ):
        cy = 1700
        o = opamp(s, "buf", x0 + 170, cy, minus_top=True, title="TLV9062", unit=unit)
        yp = o["plus"][1]
        flag(s, x0, top, src)
        two(s, "R", rt, (x0, top), (x0, yp), src, div, side="l")
        two(s, "R", rb, (x0, yp), (x0, 1820), div, "GND", side="l")
        gnd(s, x0, 1820)
        two(s, "C", cd, (x0 + 80, yp), (x0 + 80, 1820), div, "GND")
        gnd(s, x0 + 80, 1820)
        s.wire((x0, yp), o["plus"])
        s.dot(x0, yp)
        s.dot(x0 + 80, yp)
        label(s, x0 + 40, yp, div, "middle")
        s.pin("buf", pad_in, div)
        s.pin("buf", pad_neg, fbnet)
        s.pin("buf", pad_out, fbnet)

        xo = x0 + 290
        s.wire(o["out"], (xo, cy))
        s.wire((xo, cy), (xo, 1610), (x0 + 150, 1610), (x0 + 150, o["minus"][1]), o["minus"])
        s.dot(xo, cy)
        two(s, "R", rout, (xo, cy), (xo + 150, cy), fbnet, mon)
        two(s, "C", cout, (xo + 170, cy), (xo + 170, 1800), mon, "GND")
        gnd(s, xo + 170, 1800)
        s.wire((xo + 150, cy), (xo + 200, cy))
        s.dot(xo + 170, cy)
        label(s, xo + 200, cy, mon)
        s.text(x0 - 40, 1860, note, 12, color=MUTED)

    x0 = 1400
    cy = 1700
    s.wire((x0, cy), (x0 + 30, cy))
    label(s, x0, cy, "I_MON", "end")
    two(s, "R", "r_il_out", (x0 + 30, cy), (x0 + 180, cy), "I_MON", "IL_MON")
    two(s, "C", "c_il_out", (x0 + 210, cy), (x0 + 210, 1800), "IL_MON", "GND")
    gnd(s, x0 + 210, 1800)
    s.wire((x0 + 180, cy), (x0 + 250, cy))
    s.dot(x0 + 210, cy)
    label(s, x0 + 250, cy, "IL_MON")
    s.text(x0 - 60, 1860, "IL_MON = iL × 0.25V/A (13.2A で 3.3V)", 12, color=MUTED)


def aux_supply(s: Sheet) -> None:
    with s.shift(100):
        _aux_supply(s)


def _aux_supply(s: Sheet) -> None:
    s.block(1650, 1380, 700, 300, "補助電源 VIN → 12V → 3.3V")
    y = 1480
    flag(s, 1700, y, "VIN_S")
    r12 = ic(s, "reg12", 1800, 1450, 120, 80,
             left=[("VIN", 30, "3", "VIN_S")], right=[("VOUT", 30, "1", "VCC12")],
             bottom=[("GND", 60, "2", "GND")])
    s.wire((1700, y), r12["VIN"])
    two(s, "C", "c_reg12_in", (1740, y), (1740, 1580), "VIN_S", "GND")
    gnd(s, 1740, 1580)
    s.dot(1740, y)
    gnd(s, *r12["GND"])

    r33 = ic(s, "reg33", 2080, 1450, 120, 80,
             left=[("VIN", 30, "3", "VCC12")], right=[("VOUT", 30, "2,4", "3V3")],
             bottom=[("GND", 60, "1", "GND")])
    s.wire(r12["VOUT"], r33["VIN"])
    two(s, "C", "c_reg12_out", (1990, y), (1990, 1580), "VCC12", "GND")
    gnd(s, 1990, 1580)
    s.dot(1990, y)
    s.wire((2030, y), (2030, 1430))
    s.dot(2030, y)
    flag(s, 2030, 1430, "VCC12")
    gnd(s, *r33["GND"])

    s.wire(r33["VOUT"], (2320, y))
    two(s, "C", "c_reg33_out", (2260, y), (2260, 1580), "3V3", "GND")
    gnd(s, 2260, 1580)
    s.dot(2260, y)
    s.wire((2320, y), (2320, 1430))
    flag(s, 2320, 1430, "3V3")
    s.text(1680, 1665, "12V 系 約 25mA: UCC28C43, LTC7001。78L12 の損失 約 0.2W", 12, color=MUTED)


def header_and_testpoints(s: Sheet) -> None:
    with s.shift(100):
        _header_and_testpoints(s)


def _header_and_testpoints(s: Sheet) -> None:
    s.block(2380, 1380, 310, 420, "マイコン接続")
    h = ic(s, "j_mcu", 2520, 1440, 70, 250,
           left=[("1", 25, "1", "GATE_EXT"), ("3", 75, "3", "MODE"), ("5", 125, "5", "VO_MON"),
                 ("7", 175, "7", "IL_MON"), ("9", 225, "9", "VIN_MON")],
           right=[("2", 25, "2", "GND"), ("4", 75, "4", "GND"), ("6", 125, "6", "GND"),
                  ("8", 175, "8", "GND"), ("10", 225, "10", "GND")])
    for n, net in (("1", "GATE_EXT"), ("3", "MODE"), ("5", "VO_MON"), ("7", "IL_MON"), ("9", "VIN_MON")):
        label(s, *h[n], net, "end")
    s.wire(h["2"], (2640, h["2"][1]), (2640, 1730))
    for n in ("4", "6", "8", "10"):
        s.wire(h[n], (2640, h[n][1]))
        s.dot(2640, h[n][1])
    gnd(s, 2640, 1730)
    s.text(2400, 1790, "偶数ピンは全部 GND", 12, color=MUTED)

    s.block(1650, 1710, 700, 330, "LED とテストポイント")
    flag(s, 1700, 1800, "3V3")
    two(s, "R", "r_led", (1700, 1800), (1700, 1900), "3V3", "LED_A")
    two(s, "LED", "led", (1700, 1900), (1700, 1990), "LED_A", "GND", pa="2", pb="1")
    gnd(s, 1700, 1990)
    for i, (addr, net) in enumerate((("tp_imon", "I_MON"), ("tp_inp", "INP"))):
        x = 1880 + i * 110
        testpoint(s, addr, x, 1900, net)
        s.wire((x, 1900), (x, 1920))
        label(s, x, 1936, net, "middle")
    for i, addr in enumerate(("tp_gnd1", "tp_gnd2", "tp_gnd3")):
        x = 2120 + i * 70
        testpoint(s, addr, x, 1900, "GND")
        gnd(s, x, 1900)
    s.text(1880, 1770, "TP SW, VOUT はパワー段に描いた", 11, color=MUTED)


def decoupling(s: Sheet) -> None:
    s.block(30, 1900, 1700, 220, "デカップリング")
    items = (
        ("c_drv_vcc", "VCC12", "drv VCC"),
        ("c_ctl_vdd", "VCC12", "ctl VDD"),
        ("c_ctl_vdd_hf", "VCC12", "ctl VDD"),
        ("c_vref", "VREF", "ctl VREF"),
        ("c_isns", "3V3", "isns VS"),
        ("c_mux", "3V3", "mux VCC"),
        ("c_and", "3V3", "gand VCC"),
        ("c_cmp", "3V3", "cmp VCC"),
        ("c_buf", "3V3", "buf V+"),
    )
    for i, (addr, net, note) in enumerate(items):
        decap(s, addr, 90 + i * 135, 1960, net, _note(s, note))
    # U1 (TLV9062) の電源ピン。演算増幅器の記号から分けて描く
    x = 90 + len(items) * 135 + 20
    p = ic(s, "buf", x, 1970, 90, 60, title="TLV9062 電源",
           top=[("V+", 45, "8", "3V3")], bottom=[("V−", 45, "4", "GND")])
    s.wire(p["V+"], (x + 45, 1945))
    flag(s, x + 45, 1945, "3V3")
    gnd(s, *p["V−"])


def _note(s: Sheet, note: str) -> str:
    """'ctl VDD' -> 'U4 VDD', so captions follow the designators."""
    addr, pin = note.split()
    return f"{s.ref(addr)} {pin}"


def main(pcb: str, netlist_md: str, svg_path: str) -> int:
    nets, values = netlist(netlist_md)
    write(draw(designators(pcb), values), nets, svg_path)
    print(f"wrote {svg_path} (checked against {netlist_md})")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(*sys.argv[1:]))
