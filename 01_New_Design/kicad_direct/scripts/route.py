"""Local two-layer grid router using pcbnew; no external routing service.

Conservative geometric obstacles; actual acceptance is by KiCad DRC. This
router does NOT enforce USB differential impedance, coupling or skew.
"""
import heapq,math,time,json,argparse
from collections import defaultdict
import numpy as np
import pcbnew as p
from design import ROOT

STEP=.05; W=441; H=1001; PLANE=W*H
CLEAR=.137; WIDTH=.15; VIA=.55; DRILL=.25
LAYERS=[p.F_Cu,p.B_Cu]
def xy(v):return (p.ToMM(v.x)-100,p.ToMM(v.y)-100)
def vec(x,y):return p.VECTOR2I(p.FromMM(x+100),p.FromMM(y+100))
def node(x,y,z=0):return z*PLANE+int(round(y/STEP))*W+int(round(x/STEP))
def decode(n):z,k=divmod(n,PLANE);y,x=divmod(k,W);return x,y,z
def coord(n):x,y,z=decode(n);return x*STEP,y*STEP,z

import __main__
b=getattr(__main__,'ROUTER_BOARD',None)
if b is None:b=p.LoadBoard(str(ROOT/'a2_usb_uart.kicad_pcb'))
ap=argparse.ArgumentParser();ap.add_argument('--continue-existing',action='store_true');args=ap.parse_args()
if list(b.GetTracks()) and not args.continue_existing:raise SystemExit('Tracks exist: refusing to replace existing work')
items=[];pads=defaultdict(list);log=[]
for f in b.GetFootprints():
 for pad in f.Pads():
  x,y=xy(pad.GetPosition());sx,sy=map(p.ToMM,[pad.GetSize().x,pad.GetSize().y]);code=pad.GetNetCode()
  z=[0,1] if pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH] else [0]
  shape='circle' if pad.GetShape()==p.PAD_SHAPE_CIRCLE else 'rect'
  # Unnumbered NPTH is blocked on both layers; unused pads remain obstacles.
  items.append((code if code else -1,z,shape,x,y,sx,sy,pad.GetOrientationDegrees()))
  if code:pads[code].append((x,y,z,f.GetReference(),pad.GetNumber()))

def add_existing(t):
 if isinstance(t,p.PCB_VIA):
  x,y=xy(t.GetPosition());items.append((t.GetNetCode(),[0,1],'circle',x,y,p.ToMM(t.GetWidth(p.F_Cu)),p.ToMM(t.GetWidth(p.F_Cu)),0))
 else:
  a=xy(t.GetStart());c=xy(t.GetEnd());items.append((t.GetNetCode(),[LAYERS.index(t.GetLayer())],'seg',*a,*c,p.ToMM(t.GetWidth())))
for t in b.GetTracks():add_existing(t)

def draw(mask,item,margin):
 code,zs,shape,x,y,a,c,ang=item
 if shape=='seg':
  x2,y2=a,c;r=ang/2+margin;lo=(min(x,x2)-r,min(y,y2)-r);hi=(max(x,x2)+r,max(y,y2)+r)
 else:
  rad=math.radians(ang);co=math.cos(rad);si=math.sin(rad);r=max(a,c)/2+margin
  ex=abs(a/2*co)+abs(c/2*si)+margin;ey=abs(a/2*si)+abs(c/2*co)+margin
  lo=(x-ex,y-ey);hi=(x+ex,y+ey)
 ix0=max(0,int(math.floor(lo[0]/STEP)));iy0=max(0,int(math.floor(lo[1]/STEP)))
 ix1=min(W-1,int(math.ceil(hi[0]/STEP)));iy1=min(H-1,int(math.ceil(hi[1]/STEP)))
 if ix0>ix1 or iy0>iy1:return
 xx=np.arange(ix0,ix1+1)[None,:]*STEP;yy=np.arange(iy0,iy1+1)[:,None]*STEP
 if shape=='seg':
  dx=x2-x;dy=y2-y;ll=dx*dx+dy*dy
  t=np.clip(((xx-x)*dx+(yy-y)*dy)/(ll or 1),0,1)
  inside=(xx-x-t*dx)**2+(yy-y-t*dy)**2 <= r*r
 elif shape=='circle':inside=(xx-x)**2+(yy-y)**2 <= (a/2+margin)**2
 else:
  u=(xx-x)*co-(yy-y)*si;v=(xx-x)*si+(yy-y)*co
  # Round expansion of a rectangular pad, conservative for rounded corners.
  inside=np.maximum(abs(u)-a/2,0)**2+np.maximum(abs(v)-c/2,0)**2<=margin*margin
 for z in zs:mask[z,iy0:iy1+1,ix0:ix1+1]|=inside

def obstacles(net):
 mask=np.zeros((2,H,W),dtype=bool)
 for item in items:
  if item[0]!=net:draw(mask,item,(.26 if item[0]==-1 and item[2]=='circle' else CLEAR)+WIDTH/2)
 edge=math.ceil((.25+WIDTH/2)/STEP)
 mask[:,:edge,:]=True;mask[:,-edge:,:]=True;mask[:,:,:edge]=True;mask[:,:,-edge:]=True
 union=mask[0]|mask[1];via=union.copy();delta=(VIA-WIDTH)/2
 for dy in range(-5,6):
  for dx in range(-5,6):
   if math.hypot(dx,dy)*STEP>delta+STEP*.71:continue
   sy=slice(max(0,-dy),min(H,H-dy));sx=slice(max(0,-dx),min(W,W-dx))
   ty=slice(max(0,dy),min(H,H+dy));tx=slice(max(0,dx),min(W,W+dx))
   via[ty,tx]|=union[sy,sx]
 return mask.reshape(-1),via.reshape(-1)

def astar(start,goals,mask,viablock,maxvisit=150000,allow_via=True):
 goals=set(goals);gcoords=[decode(n) for n in goals]
 if not goals:return None,0
 if mask[start]:return None,0
 if len(goals)==1:
  gx,gy,gz=gcoords[0]
  def heuristic(x,y,z):
   dx=abs(x-gx);dy=abs(y-gy);return max(dx,dy)+.4142*min(dx,dy)+(8 if z!=gz else 0)
 else:
  # Lower bound using the rectangle around the current net tree.
  minx=min(q[0] for q in gcoords);maxx=max(q[0] for q in gcoords);miny=min(q[1] for q in gcoords);maxy=max(q[1] for q in gcoords)
  def heuristic(x,y,z):
   dx=max(minx-x,0,x-maxx);dy=max(miny-y,0,y-maxy);return max(dx,dy)+.4142*min(dx,dy)
 x,y,z=decode(start);heap=[(heuristic(x,y,z),0,start)];dist={start:0};prev={};vis=0
 dirs=[(-1,0,1),(1,0,1),(0,-1,1),(0,1,1),(-1,-1,1.414214),(-1,1,1.414214),(1,-1,1.414214),(1,1,1.414214)]
 while heap and vis<maxvisit:
  _,g,n=heapq.heappop(heap)
  if g>dist.get(n,1e99):continue
  vis+=1
  if n in goals:
   path=[n]
   while n in prev:n=prev[n];path.append(n)
   return path[::-1],vis
  x,y,z=decode(n)
  for dx,dy,cost in dirs:
   nx=x+dx;ny=y+dy
   if nx<0 or nx>=W or ny<0 or ny>=H:continue
   nn=n+dy*W+dx
   if mask[nn]:continue
   if dx and dy and (mask[n+dx] or mask[n+dy*W]):continue
   ng=g+cost*(1.0 if z==0 else 1.08)
   if ng<dist.get(nn,1e99):dist[nn]=ng;prev[nn]=n;heapq.heappush(heap,(ng+heuristic(nx,ny,z),ng,nn))
  if allow_via and not viablock[y*W+x]:
   nn=n+(PLANE if z==0 else -PLANE);ng=g+30
   if ng<dist.get(nn,1e99):dist[nn]=ng;prev[nn]=n;heapq.heappush(heap,(ng+heuristic(x,y,1-z),ng,nn))
 return None,vis

def track(a,c,z,net,width=WIDTH):
 if math.dist(a,c)<1e-7:return
 t=p.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*c));t.SetWidth(p.FromMM(width));t.SetLayer(LAYERS[z]);t.SetNetCode(net);b.Add(t);add_existing(t)
VIAS=[]
def via(x,y,net):
 if any(math.hypot(x-vx,y-vy)<.001 and net==vn for vx,vy,vn in VIAS):return
 VIAS.append((x,y,net))
 v=p.PCB_VIA(b);v.SetPosition(vec(x,y));v.SetWidth(p.FromMM(VIA));v.SetDrill(p.FromMM(DRILL));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(net);b.Add(v);add_existing(v)
def savepath(path,net):
 if len(path)<2:return
 start=path[0];last=path[0];direction=None
 for n in path[1:]:
  a=decode(last);c=decode(n);direct=(c[0]-a[0],c[1]-a[1],c[2]-a[2])
  if direct[2]:
   sx,sy,sz=coord(start);ex,ey,ez=coord(last);track((sx,sy),(ex,ey),sz,net);via(ex,ey,net);start=n;direction=None
  elif direction is not None and direct!=direction:
   sx,sy,sz=coord(start);ex,ey,ez=coord(last);track((sx,sy),(ex,ey),sz,net);start=last;direction=direct
  else:direction=direct
  last=n
 sx,sy,sz=coord(start);ex,ey,ez=coord(last);track((sx,sy),(ex,ey),sz,net)

if __name__ == '__main__':
 gn=b.FindNet('/GND').GetNetCode()
 # Ground pads get short local escapes and vias before signal routing.
 for x,y,zs,ref,num in pads[gn]:
  if len(zs)==2:continue
  mask,vm=obstacles(gn);start=node(x,y)
  candidates=[]
  ix,iy,_=decode(start)
  for dy in range(-36,37):
   for dx in range(-36,37):
    xx=ix+dx;yy=iy+dy
    if 0<=xx<W and 0<=yy<H and not vm[yy*W+xx]:
     distances=[math.hypot(xx*STEP-vx,yy*STEP-vy) for vx,vy,vn in VIAS]
     if not any(.001<d<.55 for d in distances):candidates.append((dx*dx+dy*dy,node(xx*STEP,yy*STEP)))
  path=None
  for _,goal in sorted(candidates)[:20]:
   path,vis=astar(start,[goal],mask,vm,maxvisit=8000,allow_via=False)
   if path:break
  if path:
   savepath(path,gn);xx,yy,zz=coord(path[-1]);via(xx,yy,gn);track((x,y),coord(path[0])[:2],0,gn)
  else:log.append({'net':'GND','pad':f'{ref}.{num}','status':'no_ground_escape'})

 def name(n):return b.FindNet(n).GetNetname().lstrip('/')
 priority={'USB_D-':0,'USB_D+':1,'XTAL_IN':2,'XTAL_OUT':3,'REF12K':4,'FB':5,'VCCA_1V8':6,'VCORE_1V8':7}
 order=sorted([n for n in pads if n!=gn],key=lambda n:(priority.get(name(n),20),len(pads[n])))
 starttime=time.time()
 for net in order:
  ps=pads[net]
  if len(ps)<2:continue
  mask,vm=obstacles(net);root=ps[0];tree={node(root[0],root[1],z) for z in root[2]};remaining=ps[1:];connections=0;failed=[]
  while remaining:
   tx=[coord(n) for n in tree]
   target=min(remaining,key=lambda q:min((q[0]-v[0])**2+(q[1]-v[1])**2 for v in tx[::max(1,len(tx)//100)]))
   remaining.remove(target);x,y,zs,ref,num=target
   path,vis=astar(node(x,y,zs[0]),tree,mask,vm)
   if path:
    savepath(path,net);track((x,y),coord(path[0])[:2],zs[0],net);tree.update(path);connections+=1
   else:failed.append(f'{ref}.{num}')
  # Anchor initial terminal to the routing grid.
  track((root[0],root[1]),coord(node(root[0],root[1]))[:2],root[2][0],net)
  result={'net':name(net),'terminals':len(ps),'connections':connections,'failed':failed}
  log.append(result);print(json.dumps(result),flush=True)
  p.SaveBoard(str(ROOT/'a2_usb_uart.kicad_pcb'),b)

 # Filled ground on both layers; KiCad does the definitive thermal/clearance fill.
 for layer in LAYERS:
  z=p.ZONE(b);z.SetLayer(layer);z.SetNetCode(gn);z.SetLocalClearance(p.FromMM(.15));z.SetThermalReliefGap(p.FromMM(.2));z.SetThermalReliefSpokeWidth(p.FromMM(.2));z.SetMinThickness(p.FromMM(.1));z.SetPadConnection(p.ZONE_CONNECTION_FULL)
  poly=z.Outline();poly.NewOutline()
  for x,y in [(100.25,100.25),(121.75,100.25),(121.75,149.75),(100.25,149.75)]:poly.Append(int(p.FromMM(x)),int(p.FromMM(y)))
  b.Add(z)
 p.SaveBoard(str(ROOT/'a2_usb_uart.kicad_pcb'),b)
 (ROOT/'reports/routing.json').write_text(json.dumps({'seconds':time.time()-starttime,'grid_mm':STEP,'width_mm':WIDTH,'clearance_margin_mm':CLEAR,'results':log,'usb_differential_constraints_enforced':False},indent=2),encoding='utf-8')
 print('Route complete',time.time()-starttime,flush=True)
