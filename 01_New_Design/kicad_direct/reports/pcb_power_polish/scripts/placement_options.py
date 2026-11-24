from geom import *
from shapely import affinity
from shapely.geometry import box
from shapely.strtree import STRtree
# Candidate positions for bulk capacitors; do not write PCB.
for ref,target,region in [('C12','C10',(102,107,109.5,111)),('C11','C9',(114.5,109.5,121,113.5)),('C2','C5',(117.5,115.5,120.5,120)),('C1','C23',(118.5,112.5,120.5,117)),('C19','C17',(112,132,116,136))]:
 f=fps[ref];old=xy(f.GetPosition());angle=f.GetOrientationDegrees();pp=[p for p in f.Pads()];net=pad(ref,1).GetNetname();geoms=[poly(p) for p in pp]
 obstacles=[poly(p).buffer(.14) for ff in fps.values() if ff.GetReference()!=ref for p in ff.Pads()]
 # Only routing of this capacitor's power net may change here. Grounds may be locally relocated.
 for t in b.GetTracks():
  if t.GetNetname() in [net,'GND']:continue
  g=Point(xy(t.GetPosition())).buffer(k.ToMM(t.GetWidth(k.F_Cu))/2+.14) if isinstance(t,k.PCB_VIA) else linegeom(t).buffer(k.ToMM(t.GetWidth())/2+.14)
  if isinstance(t,k.PCB_VIA) or t.GetLayer()==k.F_Cu:obstacles.append(g)
 # Component bodies of the large IC / crystal must remain free.
 obstacles.extend([box(107.5,112.5,114.5,119.5),box(108.8,126.4,113.2,131.6),box(114.7,106.65,117.3,109.85)])
 tree=STRtree(obstacles);found=[];dest=xy(pad(target,1).GetPosition())
 for ang in [0,90,180,270]:
  gs=[affinity.rotate(g,angle-ang,origin=old) for g in geoms]
  for ix in range(round(region[0]*4),round(region[2]*4)+1):
   for iy in range(round(region[1]*4),round(region[3]*4)+1):
    pos=(ix/4,iy/4);new=[affinity.translate(g,pos[0]-old[0],pos[1]-old[1]) for g in gs]
    if any(len(tree.query(g,predicate='intersects')) for g in new):continue
    # Check rectangular body gap as well.
    body=unary_union(new).convex_hull
    if len(tree.query(body,predicate='intersects')):continue
    power=new[0].centroid.coords[0];dist=math.dist(power,dest)
    if dist<math.dist(xy(pad(ref,1).GetPosition()),dest):found.append((round(dist,3),pos,ang))
 print(ref,sorted(found)[:12])
