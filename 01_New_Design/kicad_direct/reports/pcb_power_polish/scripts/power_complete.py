from geom import *
for t in list(b.GetTracks()):
 if uid(t)=='00788b40-80c0-4f61-b372-eeacdb92be24':remove(t)
# C19 stays next to U4: retain output->bulk->distribution, add a direct local return.
track(xy(pad('C19',2).GetPosition()),(112.45,132.725),'GND',k.F_Cu,.3);via((112.45,132.725),'GND')
for t in b.GetTracks():
 if not isinstance(t,k.PCB_VIA) and t.GetNetname()=='VIO' and t.GetLayer()==k.F_Cu:
  a=xy(t.GetStart());c=xy(t.GetEnd())
  if min(a[0],c[0])>=111.63 and max(a[0],c[0])<=113.4 and min(a[1],c[1])>=134.27 and max(a[1],c[1])<=135.25:t.SetWidth(k.FromMM(.3))
for ref,q in [('C12',(106.4,108.5)),('D5',(109,106)),('C1',(121.05,114.3)),('C2',(121.1,117.7))]:
 f=fps[ref].Reference();f.SetPosition(v(*q));f.SetTextAngle(k.EDA_ANGLE(90 if ref in ['C1','C2'] else 0,k.DEGREES_T))
from ground import stitch_ground
try:log=stitch_ground();(OUT/'ground_repair.json').write_text(json.dumps(log,indent=2))
except Exception as e:print(e)
drc('power_complete')
