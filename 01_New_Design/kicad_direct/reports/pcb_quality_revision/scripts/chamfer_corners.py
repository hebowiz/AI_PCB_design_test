from geom import *
from collections import defaultdict
import numpy as np
allowed={r['net'] for r in json.loads((OUT/'before/proposed_scope.json').read_text()) if not r['tier'].startswith('P')}
pads=[(p,poly(p)) for f in fps.values() for p in f.Pads() if p.IsOnLayer(k.F_Cu)]
log=[];skips=[]
for iteration in range(3):
 nodes=defaultdict(list)
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA) or t.GetNetname() not in allowed:continue
  for q in [xy(t.GetStart()),xy(t.GetEnd())]:nodes[(t.GetNetname(),t.GetLayer(),tuple(round(x,5) for x in q))].append(t)
 changed=0
 for (net,z,q),pair in nodes.items():
  if len(pair)!=2:continue
  t1,t2=pair
  if uid(t1)==uid(t2):continue
  # Earlier corner changes may have moved this vertex.
  if any(min(math.dist(q,xy(t.GetStart())),math.dist(q,xy(t.GetEnd())))>.00002 for t in pair):continue
  a=xy(t1.GetStart()) if math.dist(q,xy(t1.GetEnd()))<.00002 else xy(t1.GetEnd());c=xy(t2.GetStart()) if math.dist(q,xy(t2.GetEnd()))<.00002 else xy(t2.GetEnd())
  va=np.array(q)-np.array(a);vc=np.array(c)-np.array(q);la=np.linalg.norm(va);lc=np.linalg.norm(vc)
  if min(la,lc)<.035:continue
  u=va/la;v2=vc/lc;dot=float(np.dot(u,v2));ang=math.degrees(math.acos(max(-1,min(1,dot))))
  if ang<89.9 or ang>135.1:continue
  if abs(k.ToMM(t1.GetWidth())-k.ToMM(t2.GetWidth()))>.001:continue
  w=k.ToMM(t1.GetWidth());others=[t for t in b.GetTracks() if uid(t) not in [uid(t1),uid(t2)]]
  # Do not turn a T, pad, or via junction into a disconnected corner.
  if any(Point(q).distance(g)<.005 for p,g in pads if p.IsOnLayer(z)):continue
  if any(Point(q).distance(Point(xy(t.GetPosition())))<k.ToMM(t.GetWidth(k.F_Cu))/2+w/2 for t in others if isinstance(t,k.PCB_VIA)):continue
  if any(linegeom(t).distance(Point(q))<.00002 for t in others if not isinstance(t,k.PCB_VIA) and t.GetLayer()==z):continue
  done=False
  for length in [.45,.3,.2,.15,.1,.075,.05,.03]:
   d=min(length,la*.42,lc*.42)
   if d<.025:continue
   A=np.array(q)-d*u;B=np.array(q)+d*v2;new=[tuple(A)]
   if ang>100:
    sign=1 if u[0]*v2[1]-u[1]*v2[0]>0 else -1
    def rot(theta):theta=math.radians(theta);return np.array([u[0]*math.cos(theta)-u[1]*math.sin(theta),u[0]*math.sin(theta)+u[1]*math.cos(theta)])
    d1=rot(sign*45);d2=rot(sign*90);lens=np.linalg.solve(np.array([d1,d2]).T,B-A)
    if min(lens)<.015:continue
    new.append(tuple(A+d1*lens[0]))
   new.append(tuple(B));bad=False
   for aa,cc in zip(new,new[1:]):
    line=LineString([aa,cc]);copper=line.buffer(w/2)
    for p,g in pads:
     if not p.IsOnLayer(z):continue
     if g.distance(copper)<.132:bad=True;break
    if bad:break
    for t in others:
     if isinstance(t,k.PCB_VIA):g=Point(xy(t.GetPosition())).buffer(k.ToMM(t.GetWidth(k.F_Cu))/2)
     elif t.GetLayer()==z:g=linegeom(t).buffer(k.ToMM(t.GetWidth())/2)
     else:continue
     if g.distance(copper)<(.132 if t.GetNetname()!=net else .002):bad=True;break
    if bad:break
   if bad:continue
   old=[record(t1),record(t2)]
   if math.dist(q,xy(t1.GetStart()))<.00002:t1.SetStart(v(*A))
   else:t1.SetEnd(v(*A))
   if math.dist(q,xy(t2.GetStart()))<.00002:t2.SetStart(v(*B))
   else:t2.SetEnd(v(*B))
   newtracks=[track(aa,cc,net,z,w) for aa,cc in zip(new,new[1:])]
   log.append({'net':net,'at':q,'angle':ang,'before':old,'after':[record(t1),record(t2)]+[record(t) for t in newtracks if t]});changed+=1;done=True;break
  if not done:skips.append({'net':net,'at':q,'angle':ang,'uuids':[uid(t1),uid(t2)],'reason':'no local chamfer with clearance'})
 print('pass',iteration,'changed',changed,flush=True)
 if not changed:break
(OUT/'chamfers.json').write_text(json.dumps(log,indent=2),encoding='utf-8');(OUT/'chamfer_remaining.json').write_text(json.dumps(skips,indent=2),encoding='utf-8');print('unconnected',count());drc('chamfers')
