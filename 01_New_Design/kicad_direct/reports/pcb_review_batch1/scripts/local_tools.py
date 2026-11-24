"""Localized routing tools. Original generator and whole-board router are not run."""
from common import *
import types,os,heapq
import numpy as np
sys.path.insert(0,str(Path(os.environ['TEMP'])/'a2-pcb-calculation-packages'))
from scipy.ndimage import distance_transform_edt
r=types.ModuleType('local_pathfinder');r.ROOT=ROOT
source=(ROOT/'scripts/route.py').read_text().split("if __name__ == '__main__':")[0]
source=source.replace('from design import ROOT','').replace('VIA=.55; DRILL=.25','VIA=.6; DRILL=.3').replace('CLEAR=.137; WIDTH=.15','CLEAR=.145; WIDTH=.15')
import __main__
__main__.ROUTER_BOARD=b
saved_argv=sys.argv;sys.argv=['local','--continue-existing'];exec(compile(source,'original_router_definitions','exec'),r.__dict__);sys.argv=saved_argv
# No rules are relaxed for same-net vias. Keep opposite side free beneath protected signals.
reserved=[(109.7,105.85,112.3,109.1),(112.95,106.6,119.1,110.95)]
fanouts=json.loads((OUT/'fanouts.json').read_text())
def refresh():
 r.VIAS[:]=[(r.xy(t.GetPosition())[0],r.xy(t.GetPosition())[1],t.GetNetCode()) for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
 r.items[:]=[a for a in r.items if a[2] not in ['seg','circle']] # rebuilt below, including circular pads
 r.items.clear()
 for f in b.GetFootprints():
  for a in f.Pads():
   x,y=r.xy(a.GetPosition());sx,sy=xy(a.GetSize());zs=[0,1] if a.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH] else [0]
   r.items.append((a.GetNetCode() if a.GetNetCode() else -1,zs,'circle' if a.GetShape()==p.PAD_SHAPE_CIRCLE else 'rect',x,y,sx,sy,a.GetOrientationDegrees()))
 for t in b.GetTracks():r.add_existing(t)
def masks(net):
 mask=np.zeros((2,r.H,r.W),bool)
 for item in r.items:
  if item[0]!=net:r.draw(mask,item,(.26 if item[0]==-1 and item[2]=='circle' else r.CLEAR)+r.WIDTH/2)
 edge=7;mask[:,:edge]=True;mask[:,-edge:]=True;mask[:,:,:edge]=True;mask[:,:,-edge:]=True
 for x0,y0,x1,y1 in (reserved if b.FindNet(net).GetNetname()!='GND' else []):mask[1,int((y0-100)/r.STEP):int((y1-100)/r.STEP)+1,int((x0-100)/r.STEP):int((x1-100)/r.STEP)+1]=True
 vm=distance_transform_edt(~(mask[0]|mask[1]))*r.STEP < ((r.VIA-r.WIDTH)/2+r.STEP)
 # Additional same-net pad-to-via and via-to-via clearances.
 extra=np.zeros((2,r.H,r.W),bool)
 for f in b.GetFootprints():
  for a in f.Pads():
   if a.GetNetCode()!=net:continue
   x,y=r.xy(a.GetPosition());sx,sy=xy(a.GetSize());r.draw(extra,(net,[0,1],'circle' if a.GetShape()==p.PAD_SHAPE_CIRCLE else 'rect',x,y,sx,sy,a.GetOrientationDegrees()),.2+r.VIA/2+.035)
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA) and t.GetNetCode()==net:
   x,y=r.xy(t.GetPosition());r.draw(extra,(net,[0,1],'circle',x,y,.6,.6,0),.5+.3+.035)
 vm|=extra[0]|extra[1]
 if b.FindNet(net).GetNetname()!='GND':
  shaped=vm.reshape(r.H,r.W)
  for x0,y0,x1,y1 in reserved:shaped[int((y0-100-.35)/r.STEP):int((y1-100+.35)/r.STEP)+1,int((x0-100-.35)/r.STEP):int((x1-100+.35)/r.STEP)+1]=True
 # Preserve existing pad centerline as a legal conduit, while blocking side entry.
 base_mask=mask.copy()
 # Do not approach any IC pad sideways: narrow windows at short-edge escape endpoint.
 for ref in ['U1','U2','U5']:
  for a in fps[ref].Pads():
   if a.GetNetCode()!=net:continue
   key=ref+'.'+a.GetNumber()
   if key not in fanouts:continue
   x,y=r.xy(a.GetPosition());sx,sy=xy(a.GetSize());r.draw(mask,(net,[0],'rect',x,y,sx,sy,a.GetOrientationDegrees()),.12)
 for ref in ['U1','U2','U5']:
  for a in fps[ref].Pads():
   key=ref+'.'+a.GetNumber()
   if a.GetNetCode()!=net or key not in fanouts:continue
   x,y=r.xy(a.GetPosition());fx,fy=fanouts[key][0]-100,fanouts[key][1]-100;dx=fx-x;dy=fy-y
   for q in np.linspace(-1,1,81):
    ix=int(round((x+q*dx)/r.STEP));iy=int(round((y+q*dy)/r.STEP));mask[0,iy,ix]=base_mask[0,iy,ix]
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA) and t.GetNetCode()==net:
   x,y=r.xy(t.GetPosition());ix=int(round(x/r.STEP));iy=int(round(y/r.STEP))
   if not mask[0,iy,ix] and not mask[1,iy,ix]:vm[iy,ix]=False
 return mask.reshape(-1),vm.reshape(-1)

def endpoint(item):
 if isinstance(item,p.PAD):
  key=item.GetParentFootprint().GetReference()+'.'+item.GetNumber()
  if key in fanouts:return (fanouts[key][0]-100,fanouts[key][1]-100,0)
  x,y=r.xy(item.GetPosition());return x,y,0
 x,y=r.xy(item.GetPosition() if isinstance(item,p.PCB_VIA) else item.GetStart());return x,y,0 if item.IsOnLayer(p.F_Cu) else 1

def route(a,c,net,allow_via=True,targets=None):
 mask,vm=masks(net);start=r.node(*a);end=r.node(*c)
 target_map={r.node(*q):q for q in targets} if targets else {end:c}
 target_map={n:q for n,q in target_map.items() if not mask[n]}
 path,visited=r.astar(start,list(target_map),mask,vm,maxvisit=900000,allow_via=allow_via)
 if not path:return False,visited
 c=target_map[path[-1]]
 # Greedily replace grid staircases by clear 45-degree or orthogonal doglegs.
 def clearline(i,j):
  x,y,z=r.decode(i);u,v,k=r.decode(j);dx=u-x;dy=v-y
  if z!=k or (dx and dy and abs(dx)!=abs(dy)):return False
  n=max(abs(dx),abs(dy));sx=0 if not dx else (1 if dx>0 else -1);sy=0 if not dy else(1 if dy>0 else -1)
  return all(not mask[z*r.PLANE+(y+t*sy)*r.W+x+t*sx] for t in range(n+1))
 compact=[];i=0
 while i<len(path):
  compact.append(path[i]);j=i+1
  while j<len(path) and r.decode(path[j])[2]==r.decode(path[i])[2]:j+=1
  chosen=i+1
  for k in range(j-1,i+1,-1):
   x,y,z=r.decode(path[i]);u,v,_=r.decode(path[k]);dx=u-x;dy=v-y
   if clearline(path[i],path[k]):chosen=k;break
   mid_candidates=[r.node(u*r.STEP,y*r.STEP,z),r.node(x*r.STEP,v*r.STEP,z)]
   m=min(abs(dx),abs(dy));sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1
   mid_candidates += [r.node((x+sx*m)*r.STEP,(y+sy*m)*r.STEP,z),r.node((u-sx*m)*r.STEP,(v-sy*m)*r.STEP,z)]
   good=next((q for q in mid_candidates if clearline(path[i],q) and clearline(q,path[k])),None)
   if good is not None:compact.append(good);chosen=k;break
  i=chosen
 # Add compressed segments, including explicit via transitions.
 for n,m in zip(compact,compact[1:]):
  x,y,z=r.coord(n);u,v,k=r.coord(m)
  if z!=k:r.via(x,y,net)
  else:r.track((x,y),(u,v),z,net)
 # Snap endpoint to grid using <= 2 Manhattan/45 legs, never alter IC escape.
 for point,nodeval in [(a,compact[0]),(c,compact[-1])]:
  x,y,z=point;u,v,k=r.coord(nodeval)
  if abs(x-u)>1e-6 and abs(y-v)>1e-6 and abs(abs(x-u)-abs(y-v))>1e-6:
   m=min(abs(x-u),abs(y-v));sx=1 if u>x else -1;sy=1 if v>y else -1;r.track((x,y),(x+sx*m,y+sy*m),z,net);r.track((x+sx*m,y+sy*m),(u,v),z,net)
  else:r.track((x,y),(u,v),z,net)
 return True,visited
refresh()
