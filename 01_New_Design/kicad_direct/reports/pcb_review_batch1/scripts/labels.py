from common import *
pads=[a for f in fps.values() for a in f.Pads()]
refs=sorted(set(json.loads((OUT/"placement_changes.json").read_text()))|{"R12"})
def box(item):
 r=item.GetBoundingBox();return (p.ToMM(r.GetX()),p.ToMM(r.GetY()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom()))
def collide(a,c,m=.12):return a[0]<c[2]+m and a[2]>c[0]-m and a[1]<c[3]+m and a[3]>c[1]-m
obstacles=[box(a) for a in pads if a.IsOnLayer(p.F_Cu)]
for f in fps.values():
 obstacles += [box(g) for g in f.GraphicalItems() if g.GetLayer()==p.F_SilkS]
 if f.GetReference() not in refs and f.Reference().IsVisible():obstacles.append(box(f.Reference()))
log={}
for ref in refs:
 f=fps[ref];field=f.Reference();old=xy(field.GetPosition());cx,cy=xy(f.GetPosition());field.SetTextSize(v(.6,.6));field.SetTextThickness(p.FromMM(.1));field.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
 candidates=sorted((math.hypot(dx,dy)+(.4 if angle else 0),dx,dy,angle) for dx in [i*.1 for i in range(-35,36)] for dy in [i*.1 for i in range(-35,36)] for angle in [0,90])
 for _,dx,dy,angle in candidates:
  x,y=cx+dx,cy+dy;field.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));field.SetPosition(v(x,y));bb=box(field)
  if bb[0]<100.25 or bb[2]>121.75 or bb[1]<100.25 or bb[3]>149.75:continue
  if not any(collide(bb,o) for o in obstacles):break
 else:raise RuntimeError('No readable reference location '+ref)
 obstacles.append(bb);log[ref]={'before':old,'after':[x,y]}
 print('Label',ref,x,y)

save();(OUT/"reference_positions.json").write_text(json.dumps(log,indent=2));drc("labels")
