from geom import *
from collections import defaultdict
import numpy as np
log=[];skips=[]
base=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));protected={uid(t) for t in base.GetTracks()}
pads=[(p,poly(p,z),z) for f in fps.values() for p in f.Pads() for z in [0,2] if p.IsOnLayer(z)]
# Remove only copper wholly redundant within an existing pad/via or wider track.
for t in list(b.GetTracks()):
 if isinstance(t,k.PCB_VIA) or uid(t) in protected:continue
 net=t.GetNetname();z=t.GetLayer();line=linegeom(t);covered=False
 for p,g,l in pads:
  if z==l and p.GetNetname()==net and g.buffer(-.002).covers(line):covered=True;break
 if not covered:
  for o in b.GetTracks():
   if uid(o)==uid(t) or o.GetNetname()!=net:continue
   if isinstance(o,k.PCB_VIA):g=Point(xy(o.GetPosition())).buffer(k.ToMM(o.GetWidth(k.F_Cu))/2-.002)
   elif o.GetLayer()==z and o.GetWidth()>=t.GetWidth():g=linegeom(o).buffer(.00001)
   else:continue
   if g.covers(line):covered=True;break
 if covered:log.append({'removed_covered':record(t)});remove(t)
# New placements must retain octilinear GND connections.
for t in list(b.GetTracks()):
 if isinstance(t,k.PCB_VIA) or uid(t) in protected:continue
 a=xy(t.GetStart());c=xy(t.GetEnd());dx=c[0]-a[0];dy=c[1]-a[1]
 if t.GetNetname()=='GND' and abs(dx)>1e-5 and abs(dy)>1e-5 and abs(abs(dx)-abs(dy))>1e-5:
  m=min(abs(dx),abs(dy));q=(a[0]+math.copysign(m,dx),a[1]+math.copysign(m,dy));remove(t);track(a,q,'GND',t.GetLayer(),k.ToMM(t.GetWidth()));track(q,c,'GND',t.GetLayer(),k.ToMM(t.GetWidth()))
for iteration in range(4):
 nodes=defaultdict(list)
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA) or t.GetNetname() in ['/USB_D+','/USB_D-']:continue
  for q in [xy(t.GetStart()),xy(t.GetEnd())]:nodes[(t.GetNetname(),t.GetLayer(),q)].append(t)
 changed=0
 for (net,z,q),pair in nodes.items():
  if len(pair)!=2 or uid(pair[0])==uid(pair[1]):continue
  if any(min(math.dist(q,xy(t.GetStart())),math.dist(q,xy(t.GetEnd())))>.00001 for t in pair):continue
  t1,t2=pair
  if uid(t1) in protected and uid(t2) in protected:continue
  if q[1]<124.5:continue
  a=xy(t1.GetStart()) if xy(t1.GetEnd())==q else xy(t1.GetEnd());c=xy(t2.GetStart()) if xy(t2.GetEnd())==q else xy(t2.GetEnd())
  u=np.array(q)-a;vv=np.array(c)-q;la=np.linalg.norm(u);lc=np.linalg.norm(vv)
  if min(la,lc)<.0001:continue
  u/=la;vv/=lc;ang=math.degrees(math.acos(np.clip(np.dot(u,vv),-1,1)))
  if ang<89.9 or ang>135.1:continue
  w=min(k.ToMM(t.GetWidth()) for t in pair);others=[t for t in b.GetTracks() if uid(t) not in [uid(t1),uid(t2)]]
  # A true T junction cannot be trimmed without reattaching its third branch.
  if any(not isinstance(t,k.PCB_VIA) and t.GetLayer()==z and linegeom(t).distance(Point(q))<.00001 for t in others):continue
  contacts=[g for p,g,l in pads if l==z and p.GetNetname()==net and g.intersects(Point(q))]
  contacts += [Point(xy(t.GetPosition())).buffer(k.ToMM(t.GetWidth(k.F_Cu))/2) for t in others if isinstance(t,k.PCB_VIA) and t.GetNetname()==net and Point(xy(t.GetPosition())).distance(Point(q))<k.ToMM(t.GetWidth(k.F_Cu))/2]
  done=False
  for length in [.5,.35,.25,.15,.1,.075,.05,.025,.01]:
   d=min(length,la*.45,lc*.45)
   if d<.008:continue
   A=np.array(q)-d*u;B=np.array(q)+d*vv;new=[tuple(A)]
   if ang>100:
    sign=1 if u[0]*vv[1]-u[1]*vv[0]>0 else -1
    def rot(th):th=math.radians(th);return np.array([u[0]*math.cos(th)-u[1]*math.sin(th),u[0]*math.sin(th)+u[1]*math.cos(th)])
    d1=rot(sign*45);d2=rot(sign*90);ls=np.linalg.solve(np.array([d1,d2]).T,B-A)
    if min(ls)<.004:continue
    new.append(tuple(A+d1*ls[0]))
   new.append(tuple(B));newc=LineString([a]+new+[c]).buffer(w/2);bad=False
   if any(not newc.intersects(g) for g in contacts):continue
   for aa,cc in zip(new,new[1:]):
    cp=LineString([aa,cc]).buffer(w/2)
    for p,g,l in pads:
     if l!=z:continue
     if p.GetNetname()==net and (g.intersects(linegeom(t1)) or g.intersects(linegeom(t2))):continue
     if cp.distance(g)<.132:bad=True;break
    if bad:break
    for t in others:
     if t.GetNetname()==net:continue
     if isinstance(t,k.PCB_VIA):g=Point(xy(t.GetPosition())).buffer(k.ToMM(t.GetWidth(k.F_Cu))/2)
     elif t.GetLayer()==z:g=linegeom(t).buffer(k.ToMM(t.GetWidth())/2)
     else:continue
     if cp.distance(g)<.132:bad=True;break
    if bad:break
   if bad:continue
   old=[record(t1),record(t2)]
   if xy(t1.GetStart())==q:t1.SetStart(v(*A))
   else:t1.SetEnd(v(*A))
   if xy(t2.GetStart())==q:t2.SetStart(v(*B))
   else:t2.SetEnd(v(*B))
   nt=[track(aa,cc,net,z,w) for aa,cc in zip(new,new[1:])]
   log.append({'corner':q,'angle':ang,'net':net,'before':old,'after':[record(t1),record(t2)]+[record(t) for t in nt if t]});changed+=1;done=True;break
  if not done:skips.append({'net':net,'at':q,'angle':ang,'lengths':[la,lc]})
 print('pass',iteration,changed,flush=True)
 if not changed:break
(OUT/'corner_edits.json').write_text(json.dumps(log,indent=2));(OUT/'corner_skips.json').write_text(json.dumps(skips,indent=2));drc('corners')
