from pathlib import Path
import pcbnew as p,json,math
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'reports/pcb_review_batch1'
b=p.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));ds=b.GetDesignSettings();print(type(b),type(ds),flush=True);fps={f.GetReference():f for f in b.GetFootprints()}
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(v):return (p.ToMM(v.x),p.ToMM(v.y))
def pad(ref,n):return next(a for a in fps[ref].Pads() if a.GetNumber()==str(n))
def tr(a,c,net,layer=p.F_Cu,w=.18):
 if math.dist(a,c)<1e-7:return
 t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetLayer(layer);t.SetWidth(p.FromMM(w));t.SetNet(b.FindNet(net));b.Add(t);return t
# U1 unchanged; localized support component moves. Pin-1 polarity/net unchanged.
places={'Y1':(116.0,108.4,180),'C13':(118.3,109.25,180),'C14':(113.7,107.55,0),
 'C9':(112.75,110.1,90),'C10':(109.0,109.9,180),'FB1':(115.0,110.2,180),'FB2':(107.1,109.9,0),
 'C11':(119.6,110.5,0),'C12':(104.5,109.7,180),'R1':(112.8,113.6,0),
 'C3':(108.25,108.3,90),'C4':(104.9,118.75,180),'C6':(117.4,113.8,0),
 'C23':(117.5,116.1,0),'C1':(120.0,114.6,90),'C5':(117.5,117.4,0),'C2':(120.0,117.7,0),
 'C8':(117.1,118.7,0),'C7':(116.8,120.2,0),'R2':(113.0,122.4,90),'C22':(114.5,122.4,90),
 'C15':(107.7,121.5,90),'C16':(106.3,126.7,180),'C17':(115.7,126.7,0),
 'C18':(107.5,135.25,180),'C19':(113.6,135.25,0),
 'D1':(112.35,106.4,0),'D5':(109.65,106.4,180)}
places.update({'Y1':(116,108.4,90),'C13':(118.6,109.5,90),'C14':(113.3,107.7,-90),
'C9':(112.7,109.9,90),'C10':(109,110.15,180),'C3':(107.1,110.1,180),
'FB1':(115.5,112.0,90),'FB2':(107.6,108.5,0),'C11':(120.2,110.2,90),'C12':(104.3,109.8,180),'R1':(106.7,107,0),
'C1':(120.1,113.7,90),'C2':(120.0,117.0,90),'C5':(117.5,117.3,0),'C8':(117.5,118.6,0),'C7':(117.5,119.9,0),
'R14':(102.5,112.5,90),'R15':(104.0,112.5,90),'D3':(102.5,115.0,90),'D4':(104,115.0,90),
'C15':(108.8,122.05,0),'C16':(105.9,126.6,180),'C17':(116.1,126.6,0),'R4':(105,125.6,0),
'C19':(112.8,133.7,90),'D1':(112.2,107.0,0),'D5':(109.8,107.0,180)})
places.update({'C19':(113.4,133.5,90),'R7':(114.7,135.4,90),'C14':(113.35,107.7,-90),'C2':(120,117.2,90),'FB1':(117.4,111.4,0)})
oldpads={r:[(xy(a.GetPosition()),xy(a.GetSize()),a.GetNetname()) for a in fps[r].Pads()] for r in places}
changes={}
for r,(x,y,angle) in places.items():
 f=fps[r];changes[r]={'old':[*xy(f.GetPosition()),f.GetOrientationDegrees()],'new':[x,y,angle]};f.SetOrientationDegrees(angle);f.SetPosition(v(x,y))
# Clear only U1/USB/crystal block plus terminal copper at moved components.
removed=[];KEEP=list(b.GetTracks())
for t in KEEP:
 a,c=xy(t.GetStart()),xy(t.GetEnd());remove=min(a[1],c[1])<121.25
 if not remove:
  for r,ps in oldpads.items():
   if any(math.dist(a,q)<1.2 or math.dist(c,q)<1.2 for q,_,n in ps):remove=True;break
 if remove:removed.append(t.m_Uuid.AsString());b.Remove(t)
 else:
  if isinstance(t,p.PCB_VIA):t.SetWidth(p.FromMM(.6));t.SetDrill(p.FromMM(.3))
print('settings',type(ds),type(b.GetDesignSettings()),flush=True);ds.m_HasStackup=True;ds.m_SolderMaskExpansion=p.FromMM(.05)
for z in b.Zones():
 z.SetPadConnection(p.ZONE_CONNECTION_THERMAL);z.SetThermalReliefGap(p.FromMM(.2));z.SetThermalReliefSpokeWidth(p.FromMM(.18))
# U1/U2/U5 outward short-edge centered fanouts. Existing offending pad-entry copper removed.
fanouts={}
for ref in ['U1','U2','U5']:
 f=fps[ref];fc=xy(f.GetPosition())
 for a in f.Pads():
  if not a.GetNetCode() or a.GetNetname().startswith('unconnected'):continue
  q=xy(a.GetPosition());sx,sy=xy(a.GetSize());ang=math.radians(a.GetOrientationDegrees());axis=(math.cos(ang),-math.sin(ang)) if sx>=sy else (math.sin(ang),math.cos(ang))
  if (q[0]-fc[0])*axis[0]+(q[1]-fc[1])*axis[1]<0:axis=(-axis[0],-axis[1])
  if ref=='U1' and (a.GetNetname()=='GND' or a.GetNumber()=='5'):axis=(-axis[0],-axis[1])
  length=max(sx,sy)/2+.30;end=(round(q[0]+length*axis[0],4),round(q[1]+length*axis[1],4))
  current=list(b.GetTracks());KEEP.extend(current)
  for t in current:
   if not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.F_Cu and (a.HitTest(t.GetStart()) or a.HitTest(t.GetEnd())):
    removed.append(t.m_Uuid.AsString());b.Remove(t)
  tr(q,end,a.GetNetname(),w=.15 if ref=='U1' else .18);fanouts[ref+'.'+a.GetNumber()]=list(end)
# Restore open-switch pad nets (KiCad SaveBoard does not retain otherwise unused net table entries).
for f in b.GetFootprints():
 if f.GetReference() in ['SW1','SW2','SW3']:
  name='unconnected-('+f.GetReference()+('-1V8{slash}open-Pad1)' if f.GetReference()=='SW1' else '-OFF{slash}open-Pad1)')
  net=b.FindNet(name)
  if net is None:net=p.NETINFO_ITEM(b,name);b.Add(net)
  next(a for a in f.Pads() if a.GetNumber()=='1').SetNet(net)
p.SaveBoard(str(ROOT/'a2_usb_uart.kicad_pcb'),b)
pro=json.loads((OUT/'before/a2_usb_uart.kicad_pro').read_text());sett=pro['board']['design_settings'];sett['rules']['min_via_diameter']=.6;sett['rules']['min_through_hole_diameter']=.3
sett['via_dimensions']=[{'diameter':.6,'drill':.3}]
for nc in pro['net_settings']['classes']:nc['via_diameter']=.6;nc['via_drill']=.3
(ROOT/'a2_usb_uart.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
(OUT/'placement_changes.json').write_text(json.dumps(changes,indent=2));(OUT/'fanouts.json').write_text(json.dumps(fanouts,indent=2));(OUT/'removed_initial_copper.json').write_text(json.dumps(removed,indent=2))
print('moved',len(changes),'removed',len(removed),'remaining',len(list(b.GetTracks())))
