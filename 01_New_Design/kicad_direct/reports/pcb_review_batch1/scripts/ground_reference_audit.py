from common import *
z=next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer()==p.B_Cu);poly=z.GetFilledPolysList(p.B_Cu);results={}
for net in ['/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT']:
 missing=[];count=0
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA) or t.GetLayer()!=p.F_Cu or t.GetNetname()!=net:continue
  a,c=xy(t.GetStart()),xy(t.GetEnd());n=max(1,math.ceil(math.dist(a,c)/.05))
  for i in range(n+1):
   q=(a[0]+(c[0]-a[0])*i/n,a[1]+(c[1]-a[1])*i/n);count+=1
   if not poly.Contains(v(*q)):missing.append([round(x,4) for x in q])
 results[net]={'centerline_samples':count,'not_over_B_GND':missing}
(OUT/'ground_reference_samples.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
