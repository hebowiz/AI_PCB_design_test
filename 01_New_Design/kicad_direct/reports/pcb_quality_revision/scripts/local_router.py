"""Width-aware local octilinear routing for explicitly selected replacement nets."""
from geom import *
import numpy as np,heapq,time
from PIL import Image,ImageDraw
STEP=.05;W=441;H=1001;PLANE=W*H
PADGEOM=[(p,poly(p)) for f in fps.values() for p in f.Pads()]
coords=lambda q:((q[0]-100)/STEP,(q[1]-100)/STEP)
node=lambda q,z=0:z*PLANE+int(round((q[1]-100)/STEP))*W+int(round((q[0]-100)/STEP))
def decode(n):z,a=divmod(n,PLANE);y,x=divmod(a,W);return x,y,z
def world(n):x,y,z=decode(n);return (x*STEP+100,y*STEP+100),z

def draw(image,g):
 if g.is_empty:return
 import shapely
 x0,y0,x1,y1=g.bounds;ix0=max(0,math.floor((x0-100)/STEP));iy0=max(0,math.floor((y0-100)/STEP));ix1=min(W,math.ceil((x1-100)/STEP)+1);iy1=min(H,math.ceil((y1-100)/STEP)+1)
 if ix0>=ix1 or iy0>=iy1:return
 xx=np.arange(ix0,ix1)[None,:]*STEP+100;yy=np.arange(iy0,iy1)[:,None]*STEP+100
 inside=shapely.intersects_xy(g,xx,yy);old=np.asarray(image.crop((ix0,iy0,ix1,iy1)),dtype=bool)
 image.paste(Image.fromarray(old|inside),(ix0,iy0))

def masks(net,width,freepins=(),junctions=()):
 imgs=[Image.new('1',(W,H)),Image.new('1',(W,H))];vi=Image.new('1',(W,H));mar=.145+width/2
 for p,g in PADGEOM:
  for z,l in enumerate([k.F_Cu,k.B_Cu]):
   if not p.IsOnLayer(l):continue
   if p.GetNetname()==net and p.GetParentFootprint().GetReference()+'.'+p.GetNumber() in freepins:continue
   draw(imgs[z],g.buffer((.265+width/2) if p.GetAttribute()==k.PAD_ATTRIB_NPTH else mar))
  # All pad/via holes and mechanical pads remain obstacles. Same-net via separation .2.
  draw(vi,g.buffer(.5+.015 if p.GetNetname()==net else .3+(.265 if p.GetAttribute()==k.PAD_ATTRIB_NPTH else .145)))
 for t in b.GetTracks():
  own=t.GetNetname()==net
  if isinstance(t,k.PCB_VIA):
   g=Point(xy(t.GetPosition())).buffer(k.ToMM(t.GetWidth(k.F_Cu))/2)
   if own:
    # Existing via is a deliberate junction only when explicitly requested.
    clear=any(math.dist(xy(t.GetPosition()),q)<.01 for q in junctions)
    if not clear:
     for im in imgs:draw(im,g.buffer(.002+width/2))
    draw(vi,Point(xy(t.GetPosition())).buffer(1.1+.02))
   else:
    for im in imgs:draw(im,g.buffer(mar))
    draw(vi,g.buffer(.3+.145))
  else:
   g=linegeom(t).buffer(k.ToMM(t.GetWidth())/2);z=0 if t.GetLayer()==k.F_Cu else 1
   if own:
    # Own copper cannot be a second accidental branch: open only at approved junctions.
    blocked=g.buffer(width/2+.015)
    for q in junctions:blocked=blocked.difference(Point(q).buffer(1.5))
    draw(imgs[z],blocked)
   else:draw(imgs[z],g.buffer(mar));draw(vi,g.buffer(.3+.145))
 # Keep the existing USB / crystal reference regions free on B.Cu and of signal vias.
 for bounds in [(109.7,105.85,112.3,109.1),(112.95,106.6,119.1,110.95)]:
  from shapely.geometry import box
  region=box(*bounds);draw(imgs[1],region.buffer(width/2+.02));draw(vi,region.buffer(.32))
 # Protect every actual priority trace, including the connector launches.
 for t in b.GetTracks():
  if not isinstance(t,k.PCB_VIA) and t.GetLayer()==k.F_Cu and t.GetNetname() in ['/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT']:
   g=linegeom(t).buffer(k.ToMM(t.GetWidth())/2);draw(imgs[1],g.buffer(width/2+.02));draw(vi,g.buffer(.32))
 mask=np.array([np.asarray(im,dtype=bool) for im in imgs]);vm=np.asarray(vi,dtype=bool).copy()
 edge=math.ceil((.26+width/2)/STEP)
 mask[:,:edge]=True;mask[:,-edge:]=True;mask[:,:,:edge]=True;mask[:,:,-edge:]=True
 vm[:12]=True;vm[-12:]=True;vm[:,:12]=True;vm[:,-12:]=True
 return mask.reshape(-1),vm.reshape(-1)

def astar(start,end,mask,vm,allow_via=True):
 if mask[start] or mask[end]:return None,0
 gx,gy,gz=decode(end)
 def h(x,y,z):dx=abs(x-gx);dy=abs(y-gy);return max(dx,dy)+.414214*min(dx,dy)+(45 if z!=gz else 0)
 x,y,z=decode(start);heap=[(h(x,y,z),0,start)];dist={start:0};prev={};visited=0
 dirs=[(1,0,1),(1,1,1.414214),(0,1,1),(-1,1,1.414214),(-1,0,1),(-1,-1,1.414214),(0,-1,1),(1,-1,1.414214)]
 while heap and visited<700000:
  _,g,n=heapq.heappop(heap)
  if g>dist.get(n,1e99):continue
  visited+=1
  if n==end:
   path=[n]
   while n in prev:n=prev[n];path.append(n)
   return path[::-1],visited
  x,y,z=decode(n);old=prev.get(n);pd=None
  if old is not None:
   ox,oy,oz=decode(old)
   if oz==z:pd=(x-ox,y-oy)
  for dx,dy,cost in dirs:
   xx=x+dx;yy=y+dy
   if not(0<=xx<W and 0<=yy<H):continue
   nn=n+dy*W+dx
   if mask[nn] or (dx and dy and (mask[n+dx] or mask[n+dy*W])):continue
   bend=0 if pd is None or pd==(dx,dy) else 2.5
   ng=g+cost*(1 if z==0 else 1.03)+bend
   if ng<dist.get(nn,1e99):dist[nn]=ng;prev[nn]=n;heapq.heappush(heap,(ng+h(xx,yy,z),ng,nn))
  if allow_via and not vm[y*W+x]:
   nn=n+(PLANE if z==0 else -PLANE)
   if not mask[nn]:
    ng=g+45
    if ng<dist.get(nn,1e99):dist[nn]=ng;prev[nn]=n;heapq.heappush(heap,(ng+h(x,y,1-z),ng,nn))
 return None,visited

def simplify(path,mask):
 def clear(a,c):
  x,y,z=decode(a);u,v,l=decode(c);dx=u-x;dy=v-y
  if z!=l or (dx and dy and abs(dx)!=abs(dy)):return False
  n=max(abs(dx),abs(dy));sx=0 if dx==0 else(1 if dx>0 else-1);sy=0 if dy==0 else(1 if dy>0 else-1)
  return all(not mask[a+j*sy*W+j*sx] for j in range(n+1))
 out=[];i=0
 while i<len(path):
  out.append(path[i]);end=i+1
  while end<len(path) and decode(path[end])[2]==decode(path[i])[2]:end+=1
  chosen=i+1
  for j in range(end-1,i+1,-1):
   if clear(path[i],path[j]):chosen=j;break
   x,y,z=decode(path[i]);u,v,l=decode(path[j]);dx=u-x;dy=v-y;m=min(abs(dx),abs(dy));sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1
   # Prefer diagonal plus straight to avoid a large orthogonal turn.
   mids=[z*PLANE+(y+sy*m)*W+(x+sx*m),z*PLANE+(v-sy*m)*W+(u-sx*m),z*PLANE+y*W+u,z*PLANE+v*W+x]
   q=next((q for q in mids if clear(path[i],q) and clear(q,path[j])),None)
   if q is not None:out.append(q);chosen=j;break
  i=chosen
 return out

def route(a,c,net,width=.15,freepins=(),junctions=(),za=0,zc=0):
 mask,vm=masks(net,width,freepins,junctions);start=node(a,za);end=node(c,zc)
 if mask[start] or mask[end]:print('blocked endpoint',net,a,bool(mask[start]),c,bool(mask[end]),flush=True);return None
 path,visited=astar(start,end,mask,vm,True)
 if path is None:print('no path',net,a,c,'visited',visited,flush=True);return None
 path=simplify(path,mask);out=[]
 for n,m in zip(path,path[1:]):
  aa,z=world(n);cc,l=world(m)
  if z!=l:out.append(via(aa,net))
  else:
   t=track(aa,cc,net,k.F_Cu if z==0 else k.B_Cu,width)
   if t:out.append(t)
 # Orthogonal alignment for sub-grid pad centers (no arbitrary-angle nanosegments).
 for q,n in [(a,path[0]),(c,path[-1])]:
  qq,z=world(n)
  if math.dist(q,qq)>.000001:
   dx=qq[0]-q[0];dy=qq[1]-q[1];m=min(abs(dx),abs(dy));mid=(q[0]+math.copysign(m,dx),q[1]+math.copysign(m,dy))
   for aa,cc in [(q,mid),(mid,qq)]:
    t=track(aa,cc,net,k.F_Cu if z==0 else k.B_Cu,width)
    if t:out.append(t)
 print('routed',net,a,c,'new',len(out),'vis',visited,flush=True);return out
