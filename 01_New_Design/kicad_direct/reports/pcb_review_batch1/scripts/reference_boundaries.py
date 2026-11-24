from common import *
# Repair annulus contact with reserved planes by moving only the two newly routed vias.
logs=[]
for uid,new in [('3ca97993-3bdd-4c13-a4c1-873bd40c57c2',(112.625,108.65)),('4757f48f-eef5-48ac-bf41-ea15830c9193',(119.45,108.25))]:
 t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==uid);old=xy(t.GetPosition());net=t.GetNetname();t.SetPosition(v(*new));logs.append({'uuid':uid,'old':old,'new':new})
 for s in list(b.GetTracks()):
  if isinstance(s,p.PCB_VIA) or s.GetNetname()!=net:continue
  a,c=xy(s.GetStart()),xy(s.GetEnd())
  if old not in [a,c]:continue
  other=c if a==old else a;z=s.GetLayer();w=p.ToMM(s.GetWidth());remove(s)
  dx=other[0]-new[0];dy=other[1]-new[1];m=min(abs(dx),abs(dy));mid=(new[0]+(m if dx>=0 else -m),new[1]+(m if dy>=0 else -m));line([new,mid,other],net,z,w)
# Ground stitching vias maintain the reference potential, unlike signal vias.
for z in b.Zones():
 if z.GetIsRuleArea() and z.GetZoneName() in ['USB reference plane','Crystal reference plane']:z.SetDoNotAllowVias(False)
rules=ROOT/'a2_usb_uart.kicad_dru';s=rules.read_text()
if 'reference_plane_signal_vias' not in s:s+='\n(rule "reference_plane_signal_vias"\n (condition "A.Type == \'Via\' && A.NetName != \'GND\' && (A.intersectsArea(\'USB reference plane\') || A.intersectsArea(\'Crystal reference plane\'))")\n (constraint disallow via))\n'
rules.write_text(s);(OUT/'reference_boundary_repairs.json').write_text(json.dumps(logs,indent=2));save();drc('boundary')
