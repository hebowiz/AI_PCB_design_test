from common import *
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) or t.GetNetname()!='/RTS_N' or t.GetLayer()!=p.F_Cu:continue
 for get,set in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  if math.dist(xy(get()),(112.9,129.325))<.00001:set(v(113.0,129.325))
save(True)
