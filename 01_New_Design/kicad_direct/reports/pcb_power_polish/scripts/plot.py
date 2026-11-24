from geom import *
from PIL import Image,ImageDraw,ImageFont
# Read-only diagnostic drawing, generated from KiCad copper polygons.
name=sys.argv[1] if len(sys.argv)>1 else 'top';box=list(map(float,sys.argv[2:6])) if len(sys.argv)>5 else [102,106,122,120];scale=110
x0,y0,x1,y1=box;im=Image.new('RGB',(int((x1-x0)*scale),int((y1-y0)*scale)),(24,27,32));d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',18)
pt=lambda q:((q[0]-x0)*scale,(q[1]-y0)*scale)
for x in range(math.ceil(x0),math.ceil(x1)):
 d.line([pt((x,y0)),pt((x,y1))],fill=(45,48,52));d.text(pt((x+.02,y0+.02)),str(x),font=font,fill='white')
for y in range(math.ceil(y0),math.ceil(y1)):
 d.line([pt((x0,y)),pt((x1,y))],fill=(45,48,52));d.text(pt((x0+.02,y+.02)),str(y),font=font,fill='white')
colors={'USB5V':'#ff8030','+3V3':'#eedd40','VPHY':'#00e0c0','VPLL':'#e060e0','VIO':'#80ff40','GND':'#777777'}
for layer in [k.B_Cu,k.F_Cu]:
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA) or t.GetLayer()!=layer:continue
  col=colors.get(t.GetNetname(),'#ec5555') if layer==k.F_Cu else '#405995'
  d.line([pt(xy(t.GetStart())),pt(xy(t.GetEnd()))],fill=col,width=max(1,int(k.ToMM(t.GetWidth())*scale)))
for f in fps.values():
 for p in f.Pads():
  g=poly(p);geoms=[g] if g.geom_type=='Polygon' else g.geoms
  for a in geoms:d.polygon([pt(q) for q in a.exterior.coords],fill=colors.get(p.GetNetname(),'#bb5555'),outline='white')
  pos=pt(xy(p.GetPosition()));d.text(pos,p.GetNumber(),font=font,fill='black',anchor='mm')
 q=xy(f.GetPosition());d.text(pt((q[0],q[1]-.32)),f.GetReference(),font=font,fill='white',anchor='mm')
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):
  x,y=pt(xy(t.GetPosition()));r=.3*scale;d.ellipse([x-r,y-r,x+r,y+r],outline='white',fill=colors.get(t.GetNetname(),'#bb5555'));r=.15*scale;d.ellipse([x-r,y-r,x+r,y+r],fill='black')
im.save(OUT/(name+'.png'))
