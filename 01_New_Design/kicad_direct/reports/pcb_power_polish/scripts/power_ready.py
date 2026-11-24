from geom import *
for t in list(b.GetTracks()):
 if uid(t)=='52942c15-203e-4fc7-a4a9-ee01a66fbd94':remove(t)
 if t.GetNetname()=='GND' and (math.dist(xy(t.GetStart()),(112.45,132.725))<.001 or math.dist(xy(t.GetEnd()),(112.45,132.725))<.001):remove(t)
track((113.4,132.725),(112.525,132.725),'GND',k.F_Cu,.3);track((112.525,132.725),(112.2255,132.4255),'GND',k.F_Cu,.3)
from shapely.geometry import box
def bbox(item):
 r=item.GetBoundingBox();return box(k.ToMM(r.GetX()),k.ToMM(r.GetY()),k.ToMM(r.GetRight()),k.ToMM(r.GetBottom()))
for ref in ['C12','D5','C1','C2']:
 f=fps[ref];field=f.Reference();orig=xy(f.GetPosition());obs=[]
 for ff in fps.values():
  for p in ff.Pads():obs.append(poly(p).buffer(.17))
  for g in ff.GraphicalItems():
   if g.GetLayer()==k.F_SilkS:obs.append(bbox(g).buffer(.12))
  for r in [ff.Reference(),ff.Value()]:
   if r.IsVisible() and r.GetLayer()==k.F_SilkS and uid(r)!=uid(field):obs.append(bbox(r).buffer(.12))
 obstacles=unary_union(obs);found=False
 choices=sorted((math.hypot(dx,dy),dx,dy,angle) for dx in [i*.25 for i in range(-14,15)] for dy in [i*.25 for i in range(-14,15)] for angle in [0,90])
 for _,dx,dy,angle in choices:
  field.SetPosition(v(orig[0]+dx,orig[1]+dy));field.SetTextAngle(k.EDA_ANGLE(angle,k.DEGREES_T));g=bbox(field)
  if g.bounds[0]<100.15 or g.bounds[2]>121.85 or g.bounds[1]<100.15 or g.bounds[3]>149.85:continue
  if not g.intersects(obstacles):found=True;break
 print('silk',ref,found,xy(field.GetPosition()))
drc('power_ready')
