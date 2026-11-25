from common import *
for ref,dx,dy in [('U4',0,.2),('R12',.4,0)]:
 old=[(xy(p.GetPosition()),p) for p in fps[ref].Pads()];q=xy(fps[ref].GetPosition());fps[ref].SetPosition(v(q[0]+dx,q[1]+dy))
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA):continue
  for method,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   p=next((p for oq,p in old if math.dist(xy(method()),oq)<.0001),None)
   if p:setter(p.GetPosition())
for t in list(b.GetTracks()):
 if uid(t)=='5b63e311-9123-4ad5-8259-1a3a0c3aea7f':remove(t)
pts=[(101.7,128.2),(101.7,129.0),(101.1,129.6),xy(pad('C18',1).GetPosition())]
for a,c in zip(pts,pts[1:]):track(a,c,'USB5V',w=.5)
q=(115.05,131.15);via(q,'GND');track((114.95,131.275),(115.05,131.175),'GND',w=.25);track((115.05,131.175),q,'GND',w=.25)
for r,p in {'C18':(101.1,132.0),'R17':(104.7,133.05),'U4':(104.2,127.4)}.items():fps[r].Reference().SetPosition(v(*p))
drc('completion')
