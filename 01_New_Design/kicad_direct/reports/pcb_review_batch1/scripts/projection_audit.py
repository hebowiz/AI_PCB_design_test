from common import *
def dot(a,c):return a[0]*c[0]+a[1]*c[1]
def sub(a,c):return a[0]-c[0],a[1]-c[1]
def pointdist(q,a,c):
 d=sub(c,a);u=max(0,min(1,dot(sub(q,a),d)/dot(d,d))) if dot(d,d) else 0
 return math.dist(q,(a[0]+u*d[0],a[1]+u*d[1]))
def cross(a,c):return a[0]*c[1]-a[1]*c[0]
def dist(a,c,d,e):
 ac=sub(c,a);de=sub(e,d);den=cross(ac,de)
 if abs(den)>1e-12:
  u=cross(sub(d,a),de)/den;v=cross(sub(d,a),ac)/den
  if 0<=u<=1 and 0<=v<=1:return 0
 return min(pointdist(a,d,e),pointdist(c,d,e),pointdist(d,a,c),pointdist(e,a,c))
priority=['/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT'];hits=[];permitted=[]
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) or t.GetLayer()!=p.F_Cu or t.GetNetname() not in priority:continue
 for s in b.GetTracks():
  if s.GetNetname()=='GND' or (not isinstance(s,p.PCB_VIA) and s.GetLayer()!=p.B_Cu):continue
  sep=dist(xy(t.GetStart()),xy(t.GetEnd()),xy(s.GetStart()),xy(s.GetEnd()))-p.ToMM(t.GetWidth())/2-p.ToMM(s.GetWidth(p.F_Cu) if isinstance(s,p.PCB_VIA) else s.GetWidth())/2
  if sep>=0:continue
  rec={'front':t.m_Uuid.AsString(),'front_net':t.GetNetname(),'back_or_via':s.m_Uuid.AsString(),'other_net':s.GetNetname(),'projected_edge_gap_mm':round(sep,4)}
  if t.GetNetname().startswith('/USB_D') and s.GetNetname().startswith('/USB_D'):permitted.append(rec)
  else:hits.append(rec)
report={'scope':'Copper projection of every F.Cu USB/crystal segment against all B.Cu tracks and through-via rings; GND excluded. USB pair crossover permitted by user.','unexpected_overlaps':hits,'permitted_usb_pair_overlaps':permitted}
(OUT/'priority_projection_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert not hits
