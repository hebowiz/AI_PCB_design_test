from common import *
for t in b.GetTracks():
 if not isinstance(t,k.PCB_VIA) and t.GetNetname()=='VPHY' and t.GetLayer()==k.F_Cu and min(xy(t.GetStart())[0],xy(t.GetEnd())[0])>=118.25 and min(xy(t.GetStart())[1],xy(t.GetEnd())[1])<111.35:
  t.SetWidth(k.FromMM(.2))
drc('filter_width')
