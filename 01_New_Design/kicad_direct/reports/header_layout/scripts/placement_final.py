from common import *
for ref,newpos in [('U4',(104.2,129.3)),('C18',(101.1,130.4))]:
 old=[(xy(p.GetPosition()),p) for p in fps[ref].Pads()];fps[ref].SetPosition(v(*newpos))
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA):continue
  for method,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   q=xy(method());p=next((p for oq,p in old if math.dist(q,oq)<.0001),None)
   if p:setter(p.GetPosition())
for t in list(b.GetTracks()):
 if t.GetNetname()=='VIO' and (math.dist(xy(t.GetStart()),(106.15,128.2))<.01 or math.dist(xy(t.GetEnd()),(106.15,128.2))<.01):remove(t)
q=(106.55,128.2);via(q,'VIO');track((106,128.35),(106.4,128.35),'VIO',w=.3);track((106.4,128.35),q,'VIO',w=.3);track(q,(106.1,128.65),'VIO',k.B_Cu,.3);track((106.1,128.65),(106.1,129.05),'VIO',k.B_Cu,.3)
for r,p in {'C18':(101.1,131.6),'U4':(104.2,127.4),'R17':(104.7,130.9)}.items():fps[r].Reference().SetPosition(v(*p));fps[r].Reference().SetTextSize(v(.6,.6))
drc('placement_final')
