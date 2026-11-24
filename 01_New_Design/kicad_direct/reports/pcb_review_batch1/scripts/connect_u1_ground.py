from local_tools import *
start=endpoint(pad('U1',22));net=b.FindNet('GND').GetNetCode();targets=[]
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) and t.GetNetCode()==net:
  x,y=r.xy(t.GetPosition());targets.extend([(x,y,0),(x,y,1)])
targets.sort(key=lambda q:math.dist(q[:2],start[:2]));ok=False
for target in targets[:12]:
 ok,n=route(start,target,net,True)
 print('ground return',target,ok,n,flush=True)
 if ok:break
assert ok;drc('all_connected')
