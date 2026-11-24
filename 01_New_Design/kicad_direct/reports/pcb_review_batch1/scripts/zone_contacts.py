from common import *
z=next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer()==p.F_Cu);s=z.GetFilledPolysList(p.F_Cu)
for i in range(s.OutlineCount()):
 inside=lambda pt:s.Contains(pt,i)
 vs=[xy(t.GetPosition()) for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND' and inside(t.GetPosition())];ps=[f.GetReference()+'.'+a.GetNumber() for f in b.GetFootprints() for a in f.Pads() if a.GetNetname()=='GND' and inside(a.GetPosition())];print(i,'vias',vs,'pads',ps)
