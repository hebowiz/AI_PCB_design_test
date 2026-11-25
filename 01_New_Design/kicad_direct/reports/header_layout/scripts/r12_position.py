from common import *
old=[(xy(p.GetPosition()),p) for p in fps['R12'].Pads()];fps['R12'].SetPosition(v(117,136.6))
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):continue
 for method,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  p=next((p for oq,p in old if math.dist(xy(method()),oq)<.0001),None)
  if p:setter(p.GetPosition())
fps['R12'].Reference().SetPosition(v(117,135.5));fps['R12'].Reference().SetTextSize(v(.6,.6))
fps['R17'].Reference().SetPosition(v(104.7,131.0));fps['R17'].Reference().SetTextSize(v(.6,.6))
drc('r12_position')
