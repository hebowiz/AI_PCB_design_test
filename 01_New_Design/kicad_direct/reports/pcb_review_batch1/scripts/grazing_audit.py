from common import *
b.BuildConnectivity();cn=b.GetConnectivity();cross=json.loads((OUT/'escape_audit.json').read_text());uidcross={(x['pin'],x['uuid']) for x in cross};ts={t.m_Uuid.AsString():t for t in b.GetTracks()};rows=[]
for ref in ['U1','U2','U4','U5']:
 for a in fps[ref].Pads():
  sx,sy=xy(a.GetSize());cx,cy=xy(a.GetPosition());ang=math.radians(a.GetOrientationDegrees());co,si=math.cos(ang),math.sin(ang)
  def inside(pt):dx,dy=pt[0]-cx,pt[1]-cy;return abs(dx*co-dy*si)<=sx/2+.00001 and abs(dx*si+dy*co)<=sy/2+.00001
  for ct in cn.GetConnectedTracks(a):
   t=ts.get(ct.m_Uuid.AsString())
   if t is None or isinstance(t,p.PCB_VIA) or t.GetLayer()!=p.F_Cu:continue
   pin=ref+'.'+a.GetNumber();uid=t.m_Uuid.AsString()
   if (pin,uid) in uidcross or (inside(xy(t.GetStart())) and inside(xy(t.GetEnd()))):continue
   rows.append({'pin':pin,'net':a.GetNetname(),'uuid':uid,'a':xy(t.GetStart()),'b':xy(t.GetEnd())})
(OUT/'grazing_pad_contacts.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
