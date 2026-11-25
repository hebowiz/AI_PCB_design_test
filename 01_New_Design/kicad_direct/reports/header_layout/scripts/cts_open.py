from geom import *
# Revert exploratory R12 movement; retain its original placement.
old=[(xy(p.GetPosition()),p) for p in fps['R12'].Pads()];q=xy(fps['R12'].GetPosition());fps['R12'].SetPosition(v(q[0]-.4,q[1]))
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):continue
 for method,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  p=next((p for oq,p in old if math.dist(xy(method()),oq)<.0001),None)
  if p:setter(p.GetPosition())
for t in list(b.GetTracks()):
 if uid(t) in ['c99bdb13-d65c-42fa-8591-6f1e5db44251','f43772dd-f750-4f90-a481-8a1b8da39b4b','658f7e5c-1df4-458f-9a49-4bbc2530474b']:remove(t)
 elif t.GetNetname()=='/CTS_N' and max(xy(t.GetStart())[0],xy(t.GetEnd())[0])<114.6 and min(xy(t.GetStart())[1],xy(t.GetEnd())[1])>130.5 and max(xy(t.GetStart())[1],xy(t.GetEnd())[1])<132.2:
  print('CTS reroute',record(t));remove(t)
save();drc('cts_open')
