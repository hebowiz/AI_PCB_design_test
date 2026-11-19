"""Keep assembly outlines on F.Fab; place small references clear of pads."""
import math
import numpy as np
import pcbnew as p
from design import ROOT
S=40
mask=np.zeros((2001,881),dtype=bool)
def rect(bb,margin=0):
    x1=max(0,int((p.ToMM(bb.GetX())-100-margin)*S))
    y1=max(0,int((p.ToMM(bb.GetY())-100-margin)*S))
    x2=min(881,int((p.ToMM(bb.GetRight())-100+margin)*S)+1)
    y2=min(2001,int((p.ToMM(bb.GetBottom())-100+margin)*S)+1)
    return x1,y1,x2,y2
def remove_silk(f):
    for g in f.GraphicalItems():
        if g.GetLayer()==p.F_SilkS:g.SetLayer(p.F_Fab)
for path in (ROOT/'libraries/A2.pretty').glob('*.kicad_mod'):
    f=p.FootprintLoad(str(path.parent),path.stem)
    remove_silk(f);p.FootprintSave(str(path.parent),f)
b=p.LoadBoard(str(ROOT/'a2_usb_uart.kicad_pcb'))
for f in b.GetFootprints():
    remove_silk(f)
    for pad in f.Pads():
        if pad.GetLayerSet().Contains(p.F_Mask):
            x1,y1,x2,y2=rect(pad.GetBoundingBox(),.18)
            mask[y1:y2,x1:x2]=True
mask[:8,:]=True;mask[-8:,:]=True;mask[:,:8]=True;mask[:,-8:]=True
offsets=[(x*.1,y*.1) for x in range(-200,201) for y in range(-200,201)]
offsets.sort(key=lambda q:q[0]**2+q[1]**2)
for f in sorted(b.GetFootprints(),key=lambda f:(not f.GetReference().startswith(('U','J','SW')),f.GetReference())):
    ref=f.Reference();ref.SetTextSize(p.VECTOR2I(p.FromMM(.65),p.FromMM(.65)))
    ref.SetTextThickness(p.FromMM(.1));ref.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
    ref.SetLayer(p.F_SilkS);ref.SetVisible(True)
    cx,cy=map(p.ToMM,[f.GetPosition().x,f.GetPosition().y])
    cy=max(101,min(149,cy))
    for dx,dy in offsets:
        ref.SetPosition(p.VECTOR2I(p.FromMM(cx+dx),p.FromMM(cy+dy)))
        bb=ref.GetBoundingBox()
        if p.ToMM(bb.GetX())<100.2 or p.ToMM(bb.GetRight())>121.8 or p.ToMM(bb.GetY())<100.2 or p.ToMM(bb.GetBottom())>149.8:continue
        x1,y1,x2,y2=rect(bb,.08)
        if not mask[y1:y2,x1:x2].any():
            mask[y1:y2,x1:x2]=True;break
    else:raise RuntimeError('No reference position for '+f.GetReference())
p.SaveBoard(str(ROOT/'a2_usb_uart.kicad_pcb'),b)
print('Placed',len(list(b.GetFootprints())),'references on front silkscreen')
