"""Render fixed before/after PCB geometry crops from saved KiCad copper; no board mutation."""
import argparse,json,sys,math
from pathlib import Path
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--before',type=Path,required=True);ap.add_argument('--after',type=Path,required=True);ap.add_argument('--regions',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--packages',type=Path,required=True);a=ap.parse_args();sys.path.insert(0,str(a.packages))
import pcbnew as k
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
from PIL import Image,ImageDraw,ImageFont
xy=lambda q:(k.ToMM(q.x),k.ToMM(q.y))
def parts(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return [p for c in getattr(g,'geoms',[]) for p in parts(c)]
def poly(s):
 def ring(r):return [xy(r.CPoint(i)) for i in range(r.PointCount())]
 return unary_union([Polygon(ring(s.COutline(i)),[ring(s.CHole(i,j)) for j in range(s.HoleCount(i))]) for i in range(s.OutlineCount())])
def load(path):
 b=k.LoadBoard(str(path));records=[]
 for z in b.Zones():
  if not z.GetIsRuleArea():records.append((z.GetLayer(),poly(z.GetFilledPolysList(z.GetLayer())),(65,49,47) if z.GetLayer()==k.F_Cu else (35,47,75),'',None))
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA):continue
  records.append((t.GetLayer(),LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(k.ToMM(t.GetWidth())/2),(225,100,85) if t.GetLayer()==k.F_Cu else (88,130,235),'',None))
 for f in b.GetFootprints():
  for p in f.Pads():
   for layer in [k.F_Cu,k.B_Cu]:
    if p.IsOnLayer(layer):
     s=k.SHAPE_POLY_SET();p.TransformShapeToPolygon(s,layer,0,k.FromMM(.001),k.ERROR_OUTSIDE);records.append((layer,poly(s),(187,160,94),f.GetReference()+'.'+p.GetNumber(),xy(p.GetPosition())))
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA):
   for layer in [k.F_Cu,k.B_Cu]:
    records.append((layer,Point(xy(t.GetPosition())).buffer(k.ToMM(t.GetWidth(layer))/2),(205,170,85),'',None));records.append((layer,Point(xy(t.GetPosition())).buffer(k.ToMM(t.GetDrillValue())/2),(20,25,31),'',None))
 return records
before,after=load(a.before),load(a.after);regions=json.loads(a.regions.read_text());fontpath='C:/Windows/Fonts/arial.ttf';font=ImageFont.truetype(fontpath,16);titlefont=ImageFont.truetype(fontpath,22)
def render(records,r,stage):
 bounds=r['bounds'];layer=k.F_Cu if r['layer']=='F.Cu' else k.B_Cu;scale=700/(bounds[2]-bounds[0]);h=round(scale*(bounds[3]-bounds[1]));im=Image.new('RGB',(700,h+70),(20,25,31));d=ImageDraw.Draw(im);cv=lambda q:((q[0]-bounds[0])*scale,70+(q[1]-bounds[1])*scale);region=box(*bounds)
 for l,g,color,label,at in records:
  if l!=layer or not g.intersects(region):continue
  for p in parts(g.intersection(region)):
   d.polygon([cv(q) for q in p.exterior.coords],fill=color)
   for hole in p.interiors:d.polygon([cv(q) for q in hole.coords],fill=(20,25,31))
 for l,g,color,label,at in records:
  if l==layer and label and region.contains(Point(at)):d.text(cv(at),label,font=font,anchor='mm',fill='white',stroke_width=1,stroke_fill='black')
 d.rectangle((0,0,700,70),fill=(10,14,18));d.text((12,10),stage+' | '+r['title'],font=titlefont,fill='white');d.text((12,40),f"{r['layer']}  X {bounds[0]}..{bounds[2]} / Y {bounds[1]}..{bounds[3]} mm",font=font,fill='white')
 return im
rows=[]
for r in regions:
 left,right=render(before,r,'BEFORE'),render(after,r,'AFTER');row=Image.new('RGB',(1410,max(left.height,right.height)),(230,230,230));row.paste(left,(0,0));row.paste(right,(710,0));rows.append(row)
result=Image.new('RGB',(1410,sum(r.height for r in rows)+10*(len(rows)-1)),(230,230,230));y=0
for r in rows:result.paste(r,(0,y));y+=r.height+10
result.save(a.output)
