from local_router import *
# Move the 5 V approach above the bead source via: no crossing of USB signals.
for t in list(b.GetTracks()):
 a=xy(t.GetStart());c=xy(t.GetEnd())
 if t.GetNetname()=='+3V3' and isinstance(t,k.PCB_VIA) and math.dist(a,(119.25,108.4))<.001:t.SetPosition(v(120,108.2))
 elif t.GetNetname()=='+3V3' and t.GetLayer()==k.F_Cu and min(a[0],c[0])>=119.2 and max(a[1],c[1])<109.1:remove(t)
 elif t.GetNetname()=='USB5V' and t.GetLayer()==k.F_Cu and not isinstance(t,k.PCB_VIA) and min(a[0],c[0])>=115.09 and min(a[1],c[1])>=103.249 and max(a[1],c[1])<=113.9:remove(t)
for a,c in zip([(115.1,103.25),(119.2,107.35),(121.05,107.35),(121.35,107.65)],[(119.2,107.35),(121.05,107.35),(121.35,107.65),(121.35,113.9)]):track(a,c,'USB5V',k.F_Cu,.5)
track((120,108.2),(120,109.065),'+3V3',k.F_Cu,.25)
# Remove redundant one-layer vias; leave the copper bus for explicit junctions.
for t in list(b.GetTracks()):
 if isinstance(t,k.PCB_VIA) and t.GetNetname()=='+3V3' and any(math.dist(xy(t.GetPosition()),q)<.001 for q in [(113.8,117.75),(116.05,111.4)]):remove(t)
for a,c in [((118.7,116.4),(116.05,117.3)),((119.6,120.45),(118.7,116.4)),((120,108.2),(116.05,111.4))]:
 mask,vm=masks('+3V3',.2,(),(a,c));pa,vis=astar(node(a,1),node(c,1),mask,vm,False)
 print(a,c,'found',pa is not None,vis,flush=True)
 if pa is None:continue
 pp=simplify(pa,mask)
 for n,m in zip(pp,pp[1:]):
  aa,z=world(n);cc,l=world(m);track(aa,cc,'+3V3',k.B_Cu,.2)
drc('bus')
