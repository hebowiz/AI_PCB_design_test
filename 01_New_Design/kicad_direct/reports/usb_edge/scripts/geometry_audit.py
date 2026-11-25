from common import *
p=k
# Rectangular pad-boundary check, independent of the routing algorithm.
rows=[]
for ref in ['U1','U2','U4','U5']:
 for a in fps[ref].Pads():
  if not a.GetNetCode() or a.GetNetname().startswith('unconnected-'):continue
  cx,cy=xy(a.GetPosition());sx,sy=xy(a.GetSize());ang=math.radians(a.GetOrientationDegrees());co,si=math.cos(ang),math.sin(ang);L=0 if sx>=sy else 1;half=[sx/2,sy/2]
  def loc(pt):dx,dy=pt[0]-cx,pt[1]-cy;return [dx*co-dy*si,dx*si+dy*co]
  for t in b.GetTracks():
   if isinstance(t,p.PCB_VIA) or t.GetNetCode()!=a.GetNetCode() or t.GetLayer()!=p.F_Cu:continue
   x,y=loc(xy(t.GetStart())),loc(xy(t.GetEnd()))
   if math.dist(x,y)<.00001:continue
   for axis in [0,1]:
    delta=y[axis]-x[axis]
    if abs(delta)<1e-8:continue
    for sign in [-1,1]:
     u=(sign*half[axis]-x[axis])/delta
     if u<-.00001 or u>1.00001:continue
     off=x[1-axis]+u*(y[1-axis]-x[1-axis])
     if abs(off)>half[1-axis]+.00001:continue
     rows.append({'pin':ref+'.'+a.GetNumber(),'net':a.GetNetname(),'uuid':t.m_Uuid.AsString(),'short_edge':axis==L,'offset_mm':round(off,6),'ok':axis==L and abs(off)<.001})
(OUT/'escape_audit.json').write_text(json.dumps(rows,indent=2));bad=[r for r in rows if not r['ok']];print('crossings',len(rows),'noncenter',len(bad));print(json.dumps(bad,indent=2))
angles=[]
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):continue
 a,c=xy(t.GetStart()),xy(t.GetEnd());dx,dy=abs(c[0]-a[0]),abs(c[1]-a[1])
 if min(dx,dy)>.0001 and abs(dx-dy)>.0001:angles.append({'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'a':a,'b':c})
(OUT/'non45_segments.json').write_text(json.dumps(angles,indent=2));print('non45',len(angles),json.dumps(angles))
