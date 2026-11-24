from geom import *
# Resolve the trial's four copper clearance issues before reconnecting the supply tree.
for t in list(b.GetTracks()):
 if isinstance(t,k.PCB_VIA):
  if math.dist(xy(t.GetPosition()),(118.85,112.55))<.001:t.SetPosition(v(118.9,112.55))
  if t.GetNetname()=='+3V3' and math.dist(xy(t.GetPosition()),(120,108.2))<.001:t.SetPosition(v(119.25,108.4))
  continue
 a=xy(t.GetStart());c=xy(t.GetEnd());net=t.GetNetname()
 if net=='VPHY' and a[1]==111.95 and c[1]==111.95:t.SetWidth(k.FromMM(.2))
 if net=='GND':
  for old,new in [((118.85,112.55),(118.9,112.55)),((119.9,111.5),(119.95,111.5))]:
   if math.dist(a,old)<.001:t.SetStart(v(*new))
   if math.dist(c,old)<.001:t.SetEnd(v(*new))
 if net=='+3V3' and t.GetLayer()==k.F_Cu:
  if math.dist(a,(120,108.2))<.001 or math.dist(c,(120,108.2))<.001:remove(t)
  if math.dist(a,(118.9,117.85))<.001:t.SetStart(v(119.2,117.85))
  if math.dist(c,(118.9,117.85))<.001:t.SetEnd(v(119.2,117.85))
  if math.dist(a,(118.9,117.85))<.001 and math.dist(c,(120,116.75))<.001:t.SetEnd(v(120,117.05));track((120,117.05),(120,116.75),net,k.F_Cu,.15)
for a,c in zip([(119.25,108.4),(119.25,108.7),(119.615,109.065)],[(119.25,108.7),(119.615,109.065),(120,109.065)]):track(a,c,'+3V3',k.F_Cu,.25)
drc('east_clearance')
