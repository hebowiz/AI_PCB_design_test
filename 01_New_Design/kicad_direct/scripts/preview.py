"""Local engineering preview from pcbnew geometry, not a manufacturing plot."""
import sys,math
import pcbnew as pcb
from PIL import Image,ImageDraw,ImageFont
from design import ROOT
b=pcb.LoadBoard(str(ROOT/'a2_usb_uart.kicad_pcb'))
S=25; origin=(98,96)
def pt(x,y):return ((x-origin[0])*S,(y-origin[1])*S)
def pos(v):return pt(pcb.ToMM(v.x),pcb.ToMM(v.y))
im=Image.new('RGB',(26*S,64*S),'#fafafa');d=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',14)
d.rectangle([pt(100,100),pt(122,150)],fill='#143c36',outline='black',width=2)
for t in b.GetTracks():
 if isinstance(t,pcb.PCB_VIA):
  x,y=pos(t.GetPosition());r=pcb.ToMM(t.GetWidth(pcb.F_Cu))*S/2;d.ellipse([x-r,y-r,x+r,y+r],fill='#ccc188');continue
 d.line([pos(t.GetStart()),pos(t.GetEnd())],fill='#e26354' if t.GetLayer()==pcb.F_Cu else '#459dde',width=max(1,round(pcb.ToMM(t.GetWidth())*S)))
for f in b.GetFootprints():
 for g in f.GraphicalItems():
  if isinstance(g,pcb.PCB_SHAPE) and g.GetLayer() in [pcb.F_Fab,pcb.F_CrtYd]:
   col='#87ae93' if g.GetLayer()==pcb.F_Fab else '#51645c'
   if g.GetShape()==pcb.SHAPE_T_SEGMENT:d.line([pos(g.GetStart()),pos(g.GetEnd())],fill=col,width=1)
   elif g.GetShape()==pcb.SHAPE_T_RECT:
    a=pos(g.GetStart());c=pos(g.GetEnd());d.rectangle([min(a[0],c[0]),min(a[1],c[1]),max(a[0],c[0]),max(a[1],c[1])],outline=col)
 for p in f.Pads():
  x,y=pos(p.GetPosition());w=pcb.ToMM(p.GetSize().x)*S/2;h=pcb.ToMM(p.GetSize().y)*S/2;ang=math.radians(p.GetOrientationDegrees())
  poly=[(x+xx*math.cos(ang)+yy*math.sin(ang),y-xx*math.sin(ang)+yy*math.cos(ang)) for xx,yy in [(-w,-h),(w,-h),(w,h),(-w,h)]]
  col='#eee0b0' if p.GetAttribute()!=pcb.PAD_ATTRIB_NPTH else '#222222';d.polygon(poly,fill=col)
  if p.GetAttribute() in [pcb.PAD_ATTRIB_PTH,pcb.PAD_ATTRIB_NPTH]:
   r=pcb.ToMM(p.GetDrillSize().x)*S/2;d.ellipse([x-r,y-r,x+r,y+r],fill='#333333')
 x,y=pos(f.GetPosition());d.text((x,y),f.GetReference(),font=font,fill='white',anchor='mm',stroke_width=1,stroke_fill='black')
for yy in range(100,151,5):d.text((2,pt(100,yy)[1]),str(yy-100),font=font,fill='black')
im.save(ROOT/'reports/pcb_preview.png')
print(ROOT/'reports/pcb_preview.png')
