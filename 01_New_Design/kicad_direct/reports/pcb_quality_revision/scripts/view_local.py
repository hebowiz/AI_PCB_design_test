from geom import *
from PIL import Image,ImageDraw,ImageFont
bounds=tuple(map(float,sys.argv[1:5]));name=sys.argv[5];scale=160
im=Image.new('RGB',(int((bounds[2]-bounds[0])*scale),int((bounds[3]-bounds[1])*scale)),(25,29,35));d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
def pt(q):return ((q[0]-bounds[0])*scale,(q[1]-bounds[1])*scale)
for t in sorted(b.GetTracks(),key=lambda t:-t.GetLayer()):
 color=(90,120,235) if t.GetLayer()==2 else (220,95,80)
 if t.GetNetname()=='/PWREN_N':color=(255,235,35)
 if t.GetNetname()=='/RXD':color=(30,220,150)
 if isinstance(t,k.PCB_VIA):
  x,y=pt(xy(t.GetPosition()));r=.3*scale;d.ellipse((x-r,y-r,x+r,y+r),outline=color,width=3);d.text((x+3,y),t.GetNetname(),font=font,fill=color)
 else:d.line([pt(xy(t.GetStart())),pt(xy(t.GetEnd()))],fill=color,width=max(1,round(k.ToMM(t.GetWidth())*scale)))
for f in fps.values():
 for p in f.Pads():
  g=poly(p)
  if g.geom_type!='Polygon':continue
  pts=[pt(q) for q in g.exterior.coords];d.polygon(pts,fill=(125,125,125),outline=(230,230,230));q=pt(xy(p.GetPosition()));d.text(q,f.GetReference()+'.'+p.GetNumber()+' '+p.GetNetname(),fill='white',font=font,anchor='mm')
for x in range(math.ceil(bounds[0]),math.floor(bounds[2])+1):d.text(pt((x,bounds[1])),str(x),font=font,fill='white')
for y in range(math.ceil(bounds[1]),math.floor(bounds[3])+1):d.text(pt((bounds[0],y)),str(y),font=font,fill='white')
p=OUT/'images';p.mkdir(exist_ok=True);im.save(p/(name+'.png'))
