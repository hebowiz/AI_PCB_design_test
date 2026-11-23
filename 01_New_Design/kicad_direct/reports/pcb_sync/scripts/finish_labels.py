from pathlib import Path
import pcbnew as p,json,math,sys,types
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'reports/pcb_sync';path=ROOT/'a2_usb_uart.kicad_pcb';b=p.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()}
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(v):return (p.ToMM(v.x),p.ToMM(v.y))
# Four inspected dangling remnants end at removed U6 or former C12 pad/via.
ids=['b3f3ad9d-3b2c-4295-8cea-cecbd5dbdb2b','0e2d07ee-07c3-4ebb-8daf-556e433d9278','00221d9a-bc14-4a40-b3d3-efe8cbc21dee','0b982db0-436f-445c-b4c1-6a8a5f1658ba']
ts={t.m_Uuid.AsString():t for t in b.GetTracks()}
for uid in ids:assert uid in ts
(OUT/'before/before_finishing.kicad_pcb').write_bytes(path.read_bytes())
for uid in ids:b.Remove(ts[uid])
# Read-only obstacle check confirmed this off-pad location with a 0.50 mm via.
# Drill edge remains 0.075 mm beyond the D5 pad copper edge (before mask expansion).
gnd=b.FindNet('GND').GetNetCode()
via=next(t for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetCode()==gnd and math.dist(xy(t.GetPosition()),(112.25,108.7))<.001)
via.SetPosition(vec(112.25,109.15));via.SetWidth(p.FromMM(.5))
t=p.PCB_TRACK(b);t.SetStart(vec(112.25,108.7));t.SetEnd(vec(112.25,109.15));t.SetWidth(p.FromMM(.15));t.SetLayer(p.F_Cu);t.SetNetCode(gnd);b.Add(t)
pads=[a for f in fps.values() for a in f.Pads()]
print('Off-pad D5 GND via: 112.25,109.15; diameter .50; drill .25')
# Move only changed/new and directly affected reference text. No copper changes.
refs=['C1','C2','C11','C12','D1','D5','C23','TP1','TP2','R17','C9','C10','C5','R2','Y1']
def box(item):
 r=item.GetBoundingBox();return (p.ToMM(r.GetX()),p.ToMM(r.GetY()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom()))
def collide(a,c,m=.12):return a[0]<c[2]+m and a[2]>c[0]-m and a[1]<c[3]+m and a[3]>c[1]-m
obstacles=[box(a) for a in pads if a.IsOnLayer(p.F_Cu)]
for f in fps.values():
 obstacles += [box(g) for g in f.GraphicalItems() if g.GetLayer()==p.F_SilkS]
 if f.GetReference() not in refs and f.Reference().IsVisible():obstacles.append(box(f.Reference()))
log={}
for ref in refs:
 f=fps[ref];field=f.Reference();old=xy(field.GetPosition());cx,cy=xy(f.GetPosition());field.SetTextSize(vec(.6,.6));field.SetTextThickness(p.FromMM(.1));field.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
 candidates=sorted((math.hypot(dx,dy)+(.4 if angle else 0),dx,dy,angle) for dx in [i*.1 for i in range(-35,36)] for dy in [i*.1 for i in range(-35,36)] for angle in [0,90])
 for _,dx,dy,angle in candidates:
  x,y=cx+dx,cy+dy;field.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));field.SetPosition(vec(x,y));bb=box(field)
  if bb[0]<100.25 or bb[2]>121.75 or bb[1]<100.25 or bb[3]>149.75:continue
  if not any(collide(bb,o) for o in obstacles):break
 else:raise RuntimeError('No readable reference location '+ref)
 obstacles.append(bb);log[ref]={'before':old,'after':[x,y]}
 print('Label',ref,x,y)
p.SaveBoard(str(path),b)
(OUT/'finishing.json').write_text(json.dumps({'removed_uuids':ids,'ground_stitch':[xy(via.GetPosition())],'reference_positions':log},indent=2),encoding='utf8')
