"""Add bottom-side operating legend; no electrical edits."""
import pcbnew as p
from design import ROOT
b=p.LoadBoard(str(ROOT/'a2_usb_uart.kicad_pcb'))
for g in list(b.GetDrawings()):
    if isinstance(g,p.PCB_TEXT) and g.GetLayer()==p.B_SilkS:b.Remove(g)
for text,y in [('A-2 / 1.6mm / REVIEW',125),('SW1: 1=1V8 2=2V5 3=3V3',133),('SWITCH VOLTAGE UNPOWERED',135),('J3: 1 RTS# 2 CTS#',138),('3 GND 4 VIO_OUT',140),('SW2: 5V / SW3: VIO',143),('J2: 1 GND 2 TXD',146),('3 RXD 4 USB5V_OUT',148)]:
    t=p.PCB_TEXT(b);t.SetText(text);t.SetPosition(p.VECTOR2I(p.FromMM(111),p.FromMM(y)))
    t.SetLayer(p.B_SilkS);t.SetMirrored(True);t.SetTextSize(p.VECTOR2I(p.FromMM(.65),p.FromMM(.65)));t.SetTextThickness(p.FromMM(.1));b.Add(t)
p.SaveBoard(str(ROOT/'a2_usb_uart.kicad_pcb'),b)
