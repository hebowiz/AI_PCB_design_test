from geom import *
from collections import defaultdict
from PIL import Image,ImageDraw,ImageFont
nodes=defaultdict(list);out=[]
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):continue
 for q in [xy(t.GetStart()),xy(t.GetEnd())]:nodes[(t.GetNetname(),t.GetLayer(),q)].append(t)
for (net,z,q),ts in nodes.items():
 import itertools
 for a,c in itertools.combinations(ts,2):
  qa=xy(a.GetStart()) if xy(a.GetEnd())==q else xy(a.GetEnd());qc=xy(c.GetStart()) if xy(c.GetEnd())==q else xy(c.GetEnd())
  u=(qa[0]-q[0],qa[1]-q[1]);v2=(qc[0]-q[0],qc[1]-q[1]);la=math.hypot(*u);lc=math.hypot(*v2)
  if min(la,lc)<.000001:continue
  turn=180-math.degrees(math.acos(max(-1,min(1,(u[0]*v2[0]+u[1]*v2[1])/la/lc))))
  if turn<89.9:continue
  pins=[f.GetReference()+'.'+p.GetNumber() for f in fps.values() for p in f.Pads() if p.IsOnLayer(z) and poly(p,z).covers(Point(q))]
  vs=[uid(t) for t in b.GetTracks() if isinstance(t,k.PCB_VIA) and math.dist(q,xy(t.GetPosition()))<k.ToMM(t.GetWidth(k.F_Cu))/2]
  out.append(dict(net=net,at=q,layer=z,degree=len(ts),angle=round(turn,3),pins=pins,vias=vs,uuids=[uid(a),uid(c)],lengths=[la,lc]))
(OUT/'all_turns.json').write_text(json.dumps(out,indent=2));print('all',len(out),'outside',sum(not r['pins'] and not r['vias'] for r in out))
for r in out:print(r)
