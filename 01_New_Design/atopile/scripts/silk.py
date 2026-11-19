"""Place legible reference text around pads and component bodies, without copper edits."""
import json
import os
from pathlib import Path
import sys
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1]
mm=k.FromMM
vec=lambda x,y:k.VECTOR2I(mm(x),mm(y))
def bbox(o,gap=0):
    r=o.GetBoundingBox()
    return (k.ToMM(r.GetLeft())-gap,k.ToMM(r.GetTop())-gap,k.ToMM(r.GetRight())+gap,k.ToMM(r.GetBottom())+gap)
def overlap(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def main():
    b=k.LoadBoard(str(ROOT/'board/a1.kicad_pcb'));fps=list(b.GetFootprints());blocked=[]
    for f in fps:
        blocked += [bbox(p,.23) for p in f.Pads()]
        bodies=[bbox(g,.1) for g in f.GraphicalItems() if g.GetLayer()==k.F_Fab and isinstance(g,k.PCB_SHAPE)]
        if bodies:blocked.append((min(r[0] for r in bodies),min(r[1] for r in bodies),max(r[2] for r in bodies),max(r[3] for r in bodies)))
        for g in list(f.GraphicalItems()):
            if g.GetLayer()==k.F_SilkS:
                # Preserve fab/polarity documentation; use rechecked board text below.
                g.SetLayer(k.Dwgs_User)
        f.Value().SetVisible(False)
    placed={};failed=[];back=[]
    for f in sorted(fps,key=lambda f:(-len(f.GetReference()), f.GetReference())):
        t=f.Reference();t.SetVisible(True);t.SetMirrored(False);t.SetLayer(k.F_SilkS);t.SetTextSize(vec(.8,.8));t.SetTextThickness(mm(.12))
        x=k.ToMM(f.GetPosition().x);y=max(1.0,k.ToMM(f.GetPosition().y))
        # Search nearby free board space. Never place silkscreen under a body.
        candidates=[]
        for dx in range(-25,26):
            for dy in range(-25,26):
                xx=x+dx*.2; yy=y+dy*.2
                if .5<xx<21.5 and .5<yy<49.5:candidates.append((dx*dx+dy*dy,xx,yy))
        found=False
        for _,xx,yy in sorted(candidates):
            for angle in (0,90):
                t.SetTextAngleDegrees(angle);t.SetPosition(vec(xx,yy));r=bbox(t,.13)
                if r[0]<.25 or r[1]<.25 or r[2]>21.75 or r[3]>49.75:continue
                if not any(overlap(r,z) for z in blocked):
                    blocked.append(r);placed[f.GetReference()]=[round(xx,3),round(yy,3),angle];found=True;break
            if found:break
        if not found:
            # Dense front-side regions use mirrored back references. Components
            # remain on the front; this is explicitly recorded for assembly.
            t.SetLayer(k.B_SilkS);t.SetMirrored(True)
            backblocks=[bbox(p,.23) for ff in fps for p in ff.Pads() if p.IsOnLayer(k.B_Cu)]
            backblocks+=back
            for _,xx,yy in sorted(candidates):
                t.SetTextAngleDegrees(0);t.SetPosition(vec(xx,yy));r=bbox(t,.13)
                if r[0]<.25 or r[1]<.25 or r[2]>21.75 or r[3]>49.75:continue
                if not any(overlap(r,z) for z in backblocks):
                    back.append(r);placed[f.GetReference()]=[round(xx,3),round(yy,3),'B.SilkS'];found=True;break
            if not found:failed.append(f.GetReference())
    k.SaveBoard(str(ROOT/'board/a1.kicad_pcb'),b)
    (ROOT/'reports/silk_placement.json').write_text(json.dumps(dict(placed=placed,failed=failed),indent=2))
    print('References placed:',len(placed),'unplaced:',failed)
    sys.stdout.flush();os._exit(bool(failed))
if __name__=='__main__':main()
