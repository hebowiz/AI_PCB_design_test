"""One-time local synchronization of the reviewed schematic into the existing PCB.
Preserves retained objects and copper; refuses to run after PCB modification.
"""
from pathlib import Path
import pcbnew as p,json,re,hashlib,os
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'reports/pcb_sync'
boardfile=ROOT/'a2_usb_uart.kicad_pcb';base=OUT/'before/a2_usb_uart.kicad_pcb'
assert boardfile.read_bytes()==base.read_bytes(),'Refusing to overwrite an edited PCB'
d=json.loads((OUT/'before/inventory.json').read_text()); comps=d['components']; terminals=d['terminals']
b=p.LoadBoard(str(boardfile));fps={f.GetReference():f for f in b.GetFootprints()}
libroot=Path(os.environ['LOCALAPPDATA'])/'Programs/KiCad/10.0/share/kicad/footprints'
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def load_fp(name):
 lib,part=name.split(':');folder=ROOT/'libraries/A2.pretty' if lib=='A2' else libroot/(lib+'.pretty')
 f=p.FootprintLoad(str(folder),part);assert f is not None,name
 f.SetFPID(p.LIB_ID(lib,part));return f
nets={str(n):v for n,v in b.GetNetsByName().items()}
for name in sorted(set(terminals.values())):
 if name not in nets:
  net=p.NETINFO_ITEM(b,name);b.Add(net);nets[name]=net
# Global labels changed names only; preserve copper membership by mapping each old net.
def netname(old):
 if old in nets and old in terminals.values():return old
 if old.startswith('/') and old[1:] in terminals.values():return old[1:]
 if old=='/USB5V_ENABLED':return 'USB5V'
 if '{slash}' in old:return old.replace('{slash}','/')
 return old
removed_tracks=[]
for t in list(b.GetTracks()):
 if t.GetNetname()=='/QOD':removed_tracks.append(t.m_Uuid.AsString());b.Remove(t)
 elif netname(t.GetNetname()) in nets:t.SetNet(nets[netname(t.GetNetname())])
for z in b.Zones():z.SetNet(nets[netname(z.GetNetname())])
removed=[];replaced=[];added=[]
for ref,f in list(fps.items()):
 if ref not in comps:removed.append(ref);b.Remove(f);del fps[ref]
for ref,c in comps.items():
 old=fps.get(ref)
 if old is None or old.GetFPID().GetUniStringLibId()!=c['footprint']:
  f=load_fp(c['footprint']);f.SetReference(ref)
  if old:
   pos=old.GetPosition();angle=old.GetOrientationDegrees();uid=old.m_Uuid
   b.Remove(old);f.SetUuid(uid);f.SetPosition(pos);f.SetOrientationDegrees(angle);replaced.append(ref)
  else:added.append(ref)
  b.Add(f);fps[ref]=f
 f=fps[ref];f.SetValue(c['value']);f.SetPath(p.KIID_PATH('/3e3080c2-3ce4-53d0-8789-6121588a45cb/'+c['uuid']))
 f.SetDNP('dnp' in c['properties'])
 attrs=f.GetAttributes()
 if 'exclude_from_bom' in c['properties']:attrs |= p.FP_EXCLUDE_FROM_BOM
 f.SetAttributes(attrs)
 for name,value in c['fields'].items():
  if name in ['Footprint','Reference','Value']:continue
  field=f.GetField(name)
  if field:field.SetText(value)
  else:
   field=p.PCB_FIELD(f,p.FIELD_T_USER,name);field.SetText(value);field.SetVisible(False);f.Add(field)
 for pad in f.Pads():
  name=terminals.get(ref+'.'+pad.GetNumber(),'')
  pad.SetNet(nets[name] if name else b.FindNet(0))
placements={'C1':(118.6,108.5,90),'C2':(118.3,111.5,0),'C11':(107.8,105.6,0),'C12':(120.5,110.3,90),'D1':(110.55,107.85,90),'D5':(111.65,107.85,90),'C23':(116.6,116.9,90),'R17':(105.9,143.0,90),'TP1':(105.2,140.9,0),'TP2':(105.9,145.5,0)}
for ref,(x,y,a) in placements.items():
 f=fps[ref];f.SetPosition(vec(x,y));f.SetOrientationDegrees(a)
 f.Reference().SetTextSize(vec(.6,.6));f.Reference().SetTextThickness(p.FromMM(.1));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));f.Reference().SetPosition(vec(x,y-1.2));f.Value().SetVisible(False)
# Detach the short old connections at the two pins whose net actually split.
for ref,num in [('U1','40'),('SW2','2')]:
 pad=next(a for a in fps[ref].Pads() if a.GetNumber()==num)
 for t in list(b.GetTracks()):
  if isinstance(t,p.PCB_VIA) or t.GetLayer()!=p.F_Cu or t.GetNetCode()==pad.GetNetCode():continue
  if pad.HitTest(t.GetStart()) or pad.HitTest(t.GetEnd()):removed_tracks.append(t.m_Uuid.AsString());b.Remove(t)
b.BuildConnectivity();p.SaveBoard(str(boardfile),b)
(OUT/'synchronization_actions.json').write_text(json.dumps({'removed':removed,'added':added,'replaced':replaced,'placements':placements,'removed_track_uuids':removed_tracks},indent=2),encoding='utf-8')
print('SYNC',removed,added,replaced,'removed tracks',len(removed_tracks))

