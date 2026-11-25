from common import *
old=[(xy(p.GetPosition()),p) for p in fps['R12'].Pads()];fps['R12'].SetOrientationDegrees(0);fps['R12'].SetPosition(v(116.1,135.6))
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):continue
 for method,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  p=next((p for oq,p in old if math.dist(xy(method()),oq)<.0001),None)
  if p:setter(p.GetPosition())
fps['R12'].Reference().SetPosition(v(116.1,134.8));fps['R12'].Reference().SetTextAngle(k.EDA_ANGLE(0,k.DEGREES_T));fps['R12'].Reference().SetTextSize(v(.6,.6))
fps['R17'].Reference().SetPosition(v(103.0,132.0));fps['R17'].Reference().SetTextAngle(k.EDA_ANGLE(90,k.DEGREES_T))
drc('r12_horizontal')
