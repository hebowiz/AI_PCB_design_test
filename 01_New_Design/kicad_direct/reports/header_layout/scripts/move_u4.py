from common import *
for t in list(b.GetTracks()):
 if uid(t) in ['c8309dc0-50ad-470e-984b-cdb840300c85','b066968d-369f-425e-81d8-71f6c8f7a252']:remove(t)
for ref,delta in [('U4',(-.8,0)),('C18',(-.6,0))]:
 old={xy(p.GetPosition()):p for p in fps[ref].Pads()};pos=xy(fps[ref].GetPosition());fps[ref].SetPosition(v(pos[0]+delta[0],pos[1]+delta[1]))
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA):continue
  for method,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   q=xy(method())
   if q in old:setter(old[q].GetPosition())
# Replace the problematic VIO output via and its two local leads.
for t in list(b.GetTracks()):
 if t.GetNetname()=='VIO' and (math.dist(xy(t.GetStart()),(106.95,128.2))<.01 or math.dist(xy(t.GetEnd()),(106.95,128.2))<.01 or (t.GetLayer()==0 and xy(t.GetEnd())==(106.8,128.35))):remove(t)
q=(106.15,128.2);via(q,'VIO')
pts=[xy(pad('U4',5).GetPosition()),(106.0,128.35),q]
for a,c in zip(pts,pts[1:]):track(a,c,'VIO',w=.3)
track(q,(106.1,128.25),'VIO',k.B_Cu,.3);track((106.1,128.25),(106.1,129.05),'VIO',k.B_Cu,.3)
track(xy(pad('U2',3).GetPosition()),(107.1,128.025),'GND',w=.25)
track(xy(pad('U2',9).GetPosition()),(114.95,131.275),'GND',w=.25)
for r,p in {'U4':(103.8,127.4),'R17':(104.7,133.15),'C19':(108.4,134.3)}.items():fps[r].Reference().SetPosition(v(*p));fps[r].Reference().SetTextSize(v(.6,.6))
drc('move_u4')
