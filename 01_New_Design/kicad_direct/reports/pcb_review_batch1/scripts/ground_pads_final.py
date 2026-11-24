from local_tools import *
net=b.FindNet('GND').GetNetCode();logs=[]
# Stitch isolated pad returns to the bottom plane with a nearby legal via.
for ref in ['C3','C23','C8']:
 a=next(a for a in fps[ref].Pads() if a.GetNetname()=='GND');start=endpoint(a);mask,vm=masks(net);candidates=[]
 x,y,_=start
 for dx in np.arange(-2.0,2.01,.1):
  for dy in np.arange(-2.0,2.01,.1):
   q=(float(round(x+dx,2)),float(round(y+dy,2)),0);node=r.node(*q)
   if not vm[node%r.PLANE] and not mask[node] and math.hypot(dx,dy)<=2.05:candidates.append(q)
 candidates.sort(key=lambda q:math.dist(q[:2],start[:2]));ok=False
 for q in candidates[:80]:
  ok,n=route(start,q,net,False)
  if ok:
   via(q[0]+100,q[1]+100,'GND');logs.append({'ref':ref,'via':[q[0]+100,q[1]+100],'route':True});save();refresh();break
 if not ok:logs.append({'ref':ref,'route':False})
 print(logs[-1],flush=True)
# Try 45-degree thermal spokes where cardinal spokes are obstructed.
for ref in []:
 a=next(a for a in fps[ref].Pads() if a.GetNetname()=='GND');a.SetThermalSpokeAngleDegrees(45)
(OUT/'ground_pad_stitching_final.json').write_text(json.dumps(logs,indent=2));drc('ground_pads_final')
