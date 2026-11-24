from geom import *
fps['D1'].Reference().SetPosition(v(110.7,107.8))
# C10 has two intentional thermal returns; keep a full spoke length before beveling.
removed=[]
for t in list(b.GetTracks()):
 if isinstance(t,k.PCB_VIA) or t.GetNetname()!='GND' or t.GetLayer()!=0:continue
 a=xy(t.GetStart());c=xy(t.GetEnd())
 if min(a[0],c[0])>=108.89 and max(a[0],c[0])<=109.501 and min(a[1],c[1])>=108.349 and max(a[1],c[1])<=109.221:
  removed.append(record(t));remove(t)
qs=[(109.5,109.22),(108.98,109.22),(108.95,109.19),(108.95,108.9),(109.5,108.35)]
for a,c in zip(qs,qs[1:]):track(a,c,'GND',k.F_Cu,.2)
track((109.5,109.22),(109.5,108.35),'GND',k.F_Cu,.2)
(OUT/'thermal_return_rework.json').write_text(json.dumps(removed,indent=2));drc('clean')
