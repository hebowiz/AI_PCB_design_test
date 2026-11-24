from common import *
from PIL import Image,ImageDraw,ImageFont
import colorsys
scale=90;box=(100,108,122,133);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',10);colors={n.GetNetCode():tuple(int(v*255) for v in colorsys.hsv_to_rgb((i*.618)%1,.65,.9)) for i,n in enumerate(b.GetNetInfo().NetsByNetcode().values())}
def pix(q):return((q[0]-box[0])*scale,(q[1]-box[1])*scale)
for layer,name in [(p.F_Cu,'front_detail'),(p.B_Cu,'back_detail')]:
 im=Image.new('RGB',(int((box[2]-box[0])*scale),int((box[3]-box[1])*scale)),(20,20,20));d=ImageDraw.Draw(im)
 for t in b.GetTracks():
  if not t.IsOnLayer(layer):continue
  col=colors.get(t.GetNetCode(),(130,130,130))
  if isinstance(t,p.PCB_VIA):
   x,y=pix(xy(t.GetPosition()));rad=.3*scale;d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=col);d.ellipse((x-.15*scale,y-.15*scale,x+.15*scale,y+.15*scale),fill=(0,0,0))
  else:d.line([pix(xy(t.GetStart())),pix(xy(t.GetEnd()))],fill=col,width=max(1,round(p.ToMM(t.GetWidth())*scale)))
 for f in b.GetFootprints():
  for a in f.Pads():
   if not a.IsOnLayer(layer):continue
   cx,cy=xy(a.GetPosition());sx,sy=xy(a.GetSize());ang=math.radians(-a.GetOrientationDegrees());co,si=math.cos(ang),math.sin(ang)
   pts=[pix((cx+dx*co-dy*si,cy+dx*si+dy*co)) for dx,dy in [(-sx/2,-sy/2),(sx/2,-sy/2),(sx/2,sy/2),(-sx/2,sy/2)]];d.polygon(pts,fill=colors.get(a.GetNetCode(),(80,80,80)));x,y=pix((cx,cy));d.text((x-25,y-5),f.GetReference()+'.'+a.GetNumber()+' '+a.GetNetname(),font=font,fill='white')
 for x in range(100,123):d.text(pix((x,108)),str(x),font=font,fill='white')
 for y in range(108,134):d.text(pix((100,y)),str(y),font=font,fill='white')
 im.save(OUT/'after'/(name+'.png'))
