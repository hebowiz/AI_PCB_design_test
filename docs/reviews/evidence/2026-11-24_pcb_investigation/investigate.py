from pathlib import Path
import pcbnew as p,json,math,collections,hashlib,subprocess,tempfile,shutil
SRC=Path('C:/Users/hebow/.codex/worktrees/a2-pcb-sync/99_AI_PCB_design_test/01_New_Design/kicad_direct');OUT=Path(__file__).resolve().parent
BASE='a300e1c7cd89654fd2800c1bc7b8bad59dae5516';repo=SRC.parents[1]
for suffix in ['kicad_pcb','kicad_pro','kicad_sch']:
 rel='01_New_Design/kicad_direct/a2_usb_uart.'+suffix
 assert subprocess.check_output(['git','hash-object','--path='+rel,rel],cwd=repo)==subprocess.check_output(['git','rev-parse',BASE+':'+rel],cwd=repo)
b=p.LoadBoard(str(SRC/'a2_usb_uart.kicad_pcb'));tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)];vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)];fps={f.GetReference():f for f in b.GetFootprints()};pads=[a for f in fps.values() for a in f.Pads() if a.IsOnLayer(p.F_Cu)]
def xy(v):return [round(p.ToMM(v.x),6),round(p.ToMM(v.y),6)]
def uid(v):return v.m_Uuid.AsString()
def pd(a):return {'ref':a.GetParentFootprint().GetReference(),'pad':a.GetNumber(),'xy':xy(a.GetPosition()),'size':xy(a.GetSize()),'angle':a.GetOrientationDegrees(),'net':a.GetNetname()}
def td(t):return {'uuid':uid(t),'net':t.GetNetname(),'start':xy(t.GetStart()),'end':xy(t.GetEnd()),'layer':b.GetLayerName(t.GetLayer()),'width':round(p.ToMM(t.GetWidth()),6)}
def dist(a,z):return math.dist(xy(a),xy(z))
vp=[]
for v in vias:
 for a in pads:
  if v.GetNetCode()!=a.GetNetCode():continue
  sh=a.GetEffectiveShape(p.F_Cu);vs=v.GetEffectiveShape(p.F_Cu)
  if sh.Collide(vs,p.FromMM(.2)):
   vp.append({'via':uid(v),'xy':xy(v.GetPosition()),'pad':pd(a),'overlap':bool(sh.Collide(vs,0))})
vv=[]
for k,v in enumerate(vias):
 for w in vias[k+1:]:
  if v.GetNetCode()!=w.GetNetCode():continue
  clearance=dist(v.GetPosition(),w.GetPosition())-p.ToMM(v.GetWidth(p.F_Cu)+w.GetWidth(p.F_Cu))/2
  if clearance<.5-1e-6:vv.append({'a':uid(v),'b':uid(w),'net':v.GetNetname(),'a_xy':xy(v.GetPosition()),'b_xy':xy(w.GetPosition()),'ring_gap':round(clearance,6)})
angle_bad=[];small=[];angles=collections.Counter()
for t in tracks:
 a=xy(t.GetStart());z=xy(t.GetEnd());dx=z[0]-a[0];dy=z[1]-a[1];ang=math.degrees(math.atan2(dy,dx))%180;angles[round(ang,2)]+=1
 if min(ang%45,45-ang%45)>.02:angle_bad.append(td(t))
 if math.hypot(dx,dy)<.3:small.append(td(t))
def cross(t,u):
 a,z=xy(t.GetStart()),xy(t.GetEnd());c,d=xy(u.GetStart()),xy(u.GetEnd())
 def side(v,w,x):return (w[0]-v[0])*(x[1]-v[1])-(w[1]-v[1])*(x[0]-v[0])
 return side(a,z,c)*side(a,z,d)<-1e-12 and side(c,d,a)*side(c,d,z)<-1e-12
signals={}
for net in ['/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT']:
 tt=[t for t in tracks if t.GetNetname()==net];crosses=[]
 for t in tt:
  for u in tracks:
   if u.GetLayer()!=t.GetLayer() and u.GetNetname() not in [net,'GND'] and cross(t,u):crosses.append({'signal':td(t),'other':td(u)})
 signals[net]={'track_total_mm':round(sum(p.ToMM(t.GetLength()) for t in tt),4),'layer_total_mm':{b.GetLayerName(l):round(sum(p.ToMM(t.GetLength()) for t in tt if t.GetLayer()==l),4) for l in [p.F_Cu,p.B_Cu]},'widths':dict(collections.Counter(round(p.ToMM(t.GetWidth()),4) for t in tt)),'vias':sum(v.GetNetname()==net for v in vias),'opposite_layer_centerline_crossings':crosses}
# Geometric screening of U1 escape edges, not a complete fanout DRC.
escapes=[]
for a in fps['U1'].Pads():
 center=xy(a.GetPosition());sx,sy=xy(a.GetSize());theta=math.radians(a.GetOrientationDegrees())
 def local(v):
  x,y=xy(v);x-=center[0];y-=center[1];return [x*math.cos(theta)-y*math.sin(theta),x*math.sin(theta)+y*math.cos(theta)]
 for t in tracks:
  if t.GetLayer()!=p.F_Cu or t.GetNetCode()!=a.GetNetCode():continue
  ends=[t.GetStart(),t.GetEnd()];inside=[a.HitTest(x) for x in ends]
  if inside.count(True)!=1:continue
  q,r=local(ends[inside.index(True)]),local(ends[inside.index(False)]);dx=r[0]-q[0];dy=r[1]-q[1];hits=[]
  for axis,half in [(0,sx/2),(1,sy/2)]:
   dd=dx if axis==0 else dy
   if abs(dd)<1e-8:continue
   for edge in [-half,half]:
    u=(edge-q[axis])/dd
    other=q[1-axis]+u*(dy if axis==0 else dx)
    if 0<=u<=1 and abs(other)<=(sy/2 if axis==0 else sx/2)+1e-6:hits.append((u,axis,other))
  if not hits:continue
  _,axis,offset=max(hits);short_axis=0 if sx>=sy else 1
  escapes.append({'pad':a.GetNumber(),'track':uid(t),'edge':'short' if axis==short_axis else 'long','offset_mm':round(offset,4),'compliant_geometric':axis==short_axis and abs(offset)<=.001})
# Straight-line distance is a placement indicator, not routed loop length.
capmap={'C1':[('U1','40')],'C23':[('U1','40')],'C2':[('U1','39')],'C3':[('U1','12')],'C4':[('U1','24')],'C5':[('U1','39')],'C6':[('U1','46')],'C7':[('U1','37')],'C8':[('U1','38')],'C9':[('U1','3')],'C10':[('U1','8')],'C11':[('U1','3')],'C12':[('U1','8')],'C15':[('U5','8')],'C16':[('U2','1')],'C17':[('U2','16')],'C18':[('U4','1')],'C19':[('U4','5')]}
capdist=[]
for ref,targets in capmap.items():
 cap=next(a for a in fps[ref].Pads() if a.GetNetname()!='GND')
 for u,n in targets:
  pin=next(a for a in fps[u].Pads() if a.GetNumber()==n)
  capdist.append({'cap':ref,'target':u+'.'+n,'straight_distance_mm':round(dist(cap.GetPosition(),pin.GetPosition()),3),'cap_pad':pd(cap),'ic_pad':pd(pin),'same_net':cap.GetNetCode()==pin.GetNetCode(),'DNP':fps[ref].IsDNP()})
mask=collections.Counter(round(p.ToMM(a.GetSolderMaskExpansion(p.F_Mask)),5) for a in pads)
zoneinfo=[{'net':z.GetNetname(),'layer':b.GetLayerName(z.GetLayer()),'connection':z.GetPadConnection(),'gap':p.ToMM(z.GetThermalReliefGap()),'spoke':p.ToMM(z.GetThermalReliefSpokeWidth())} for z in b.Zones()]
settings=json.loads((SRC/'a2_usb_uart.kicad_pro').read_text())
result={'base':BASE,'sha256':hashlib.sha256((SRC/'a2_usb_uart.kicad_pcb').read_bytes()).hexdigest(),'components':len(fps),'tracks':len(tracks),'vias':len(vias),'via_dimensions':dict(collections.Counter(f'{p.ToMM(v.GetDrillValue())}/{p.ToMM(v.GetWidth(p.F_Cu))}' for v in vias)),'through_vias':sum(v.GetViaType()==p.VIATYPE_THROUGH for v in vias),'plated_through_pads':[pd(a) for a in pads if a.GetAttribute()==p.PAD_ATTRIB_PTH],'via_pad_same_net_under_0_2':vp,'via_via_same_net_under_0_5':vv,'non_45_segments':angle_bad,'segments_under_0_3mm':small,'signals':signals,'u1_escape_screen':escapes,'capacitor_distances':capdist,'mask_expansion':dict(mask),'zones':zoneinfo,'pad_zone_overrides':dict(collections.Counter(a.GetZoneConnectionOverrides() for a in pads)),'net_settings':settings['net_settings'],'rules':settings['board']['design_settings']['rules'],'custom_rules_exist':(SRC/'a2_usb_uart.kicad_dru').exists(),'stackup_present':'(stackup' in (SRC/'a2_usb_uart.kicad_pcb').read_text(),'placement':{ref:{'xy':xy(f.GetPosition()),'angle':f.GetOrientationDegrees()} for ref,f in fps.items()},'zone_enums':{n:getattr(p,n) for n in dir(p) if n.startswith('ZONE_CONNECTION_')}}
(OUT/'geometry.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k in ['components','tracks','vias','via_dimensions','through_vias','mask_expansion','zones','pad_zone_overrides','custom_rules_exist','stackup_present','zone_enums']},indent=2))
print('pad/via',len(vp),'overlap',sum(x['overlap'] for x in vp),'via/via',len(vv),'non45',len(angle_bad),'short',len(small),'escapes',len(escapes),'offcenter',sum(not x['compliant_geometric'] for x in escapes))
for n,s in signals.items():print(n,{k:v for k,v in s.items() if k!='opposite_layer_centerline_crossings'},'crossings',len(s['opposite_layer_centerline_crossings']))
for c in capdist:print(c['cap'],c['target'],c['straight_distance_mm'],c['same_net'])
# Test proposed constraints only in a disposable copy; never save/re-fill the design.
tmp=Path(tempfile.mkdtemp(prefix='a2-review-r0017-'));print('TEMP',tmp)
for suffix in ['kicad_pcb','kicad_pro']:shutil.copyfile(SRC/('a2_usb_uart.'+suffix),tmp/('a2_usb_uart.'+suffix))
shutil.copyfile(SRC/'fp-lib-table',tmp/'fp-lib-table')
shutil.copytree(SRC/'libraries',tmp/'libraries')
rules='''(version 1)
(rule "R0018_through_via_size"
 (condition "A.Type == 'Via' && A.Via_Type == 'Through'")
 (constraint hole_size (min 0.3mm) (max 0.3mm))
 (constraint via_diameter (min 0.5mm) (max 0.5mm)))
(rule "R0019_same_net_pad_via"
 (layer outer)
 (condition "A.Net == B.Net && ((A.Type == 'Pad' && B.Type == 'Via' && B.Via_Type == 'Through') || (B.Type == 'Pad' && A.Type == 'Via' && A.Via_Type == 'Through'))")
 (constraint physical_clearance (min 0.2mm)))
(rule "R0020_same_net_via_via"
 (layer outer)
 (condition "A.Net == B.Net && A.Type == 'Via' && B.Type == 'Via' && A.Via_Type == 'Through' && B.Via_Type == 'Through'")
 (constraint physical_clearance (min 0.5mm)))
'''
(tmp/'a2_usb_uart.kicad_dru').write_text(rules);(OUT/'proposed_rules.txt').write_text(rules)
cli=Path.home()/'AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe'
cmd=[str(cli),'pcb','drc','--format','json','--severity-all','-o',str(OUT/'proposed_rules_drc.json'),str(tmp/'a2_usb_uart.kicad_pcb')]
r=subprocess.run(cmd,capture_output=True,text=True);(OUT/'rule_trial_log.txt').write_text(' '.join(cmd)+'\n'+r.stdout+r.stderr,encoding='utf8');print('DRC trial',r.returncode,r.stdout[-600:],r.stderr[-600:]);assert r.returncode==0
trial=json.loads((OUT/'proposed_rules_drc.json').read_text());print('Trial violations',len(trial['violations']),collections.Counter(v['type'] for v in trial['violations']))
assert hashlib.sha256((SRC/'a2_usb_uart.kicad_pcb').read_bytes()).hexdigest()==result['sha256']
