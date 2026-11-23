from pathlib import Path
import pcbnew as p,json,math
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'reports/pcb_sync';b=p.LoadBoard(str(ROOT/'a2_usb_uart.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(v):return(p.ToMM(v.x),p.ToMM(v.y))
def box(f):
 r=f.GetCourtyard(p.F_Cu).BBox();return [p.ToMM(r.GetX()),p.ToMM(r.GetY()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom())]
def overlap(a,c):return a[0]<c[2]+.04 and a[2]>c[0]-.04 and a[1]<c[3]+.04 and a[3]>c[1]-.04
# Regions bounded around altered functional circuits, never move I/O or switches.
specs={
 'C2':((118.3,111.5),(117,120,110.5,112.5),[0,180]),
 'C1':((118.6,108.5),(116.5,120.5,106.5,110),[0,90,180,270]),
 'C12':((113.5,108),(101.3,120.6,101.5,110),[0,90,180,270]),
 'C11':((104,105),(101.3,109.5,102,110),[0,90,180,270]),
 'D1':((110.65,107.925),(109.7,111,106.9,108.6),[0,90,180,270]),
 'D5':((111.35,107.925),(110.9,112,106.9,109),[0,90,180,270]),
 'C23':((116.9,117.25),(116.6,117.3,116,117.5),[90,270,0,180]),
 'TP1':((103,135.8),(101.5,106.5,131.5,136.5),[0]),
 'TP2':((106,135.8),(101.5,106.5,131.5,136.5),[0]),
 'R17':((104.5,134),(101.5,106.5,132,136.2),[0,90,180,270])}
fixed={ref:f for ref,f in fps.items() if ref not in specs}
log={}
tracks=list(b.GetTracks())
for ref,(target,limits,angles) in specs.items():
 f=fps[ref];best=None
 for a in angles:
  f.SetOrientationDegrees(a)
  for ix in range(round(limits[0]*10),round(limits[1]*10)+1,2):
   for iy in range(round(limits[2]*10),round(limits[3]*10)+1,2):
    x,y=ix/10,iy/10;f.SetPosition(vec(x,y));bb=box(f)
    if bb[0]<100.3 or bb[2]>121.7 or bb[1]<100.3 or bb[3]>149.7 or any(overlap(bb,box(v)) and f.GetCourtyard(p.F_Cu).Collide(v.GetCourtyard(p.F_Cu),p.FromMM(.04)) for v in fixed.values()):continue
    score=math.dist((x,y),target)*.8;hits=[]
    for pad in f.Pads():
     shape=pad.GetEffectiveShape(p.F_Cu)
     for t in tracks:
      if t.GetNetCode()==pad.GetNetCode() or not t.IsOnLayer(p.F_Cu):continue
      # C++ geometric distance with routing clearance.
      if shape.Collide(t.GetEffectiveShape(p.F_Cu),p.FromMM(.15)):
       score+= 2 if isinstance(t,p.PCB_VIA) else .1+min(2,p.ToMM(t.GetLength()))*.25
       hits.append(t.m_Uuid.AsString())
    if best is None or score<best[0]:best=(score,x,y,a,hits)
 if best is None:raise RuntimeError('No local placement '+ref)
 _,x,y,a,hits=best;f.SetPosition(vec(x,y));f.SetOrientationDegrees(a);fixed[ref]=f
 f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));f.Reference().SetPosition(vec(x,y-1.6))
 log[ref]={'pos':[x,y],'angle':a,'score':best[0],'conflicting_copper':hits}
 print(ref,log[ref],flush=True)
# KiCad internally escapes '/' in unconnected-net names.
for ref in ['SW1','SW2','SW3']:
 pad=next(a for a in fps[ref].Pads() if a.GetNumber()=='1');name=pad.GetNetname().replace('/','{slash}');pad.SetNet(b.FindNet(name))
p.SaveBoard(str(ROOT/'a2_usb_uart.kicad_pcb'),b)
(OUT/'local_placement.json').write_text(json.dumps(log,indent=2),encoding='utf8')
