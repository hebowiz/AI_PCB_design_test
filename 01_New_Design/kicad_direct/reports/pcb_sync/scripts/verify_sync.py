"""Read-only acceptance checks for the localized PCB synchronization."""
from pathlib import Path
from collections import Counter,defaultdict
import json,xml.etree.ElementTree as E,subprocess,hashlib,pcbnew as p
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT.parents[1];OUT=ROOT/'reports/pcb_sync';BASE='fffbcdbe41bad236baee48d88cf96b95f27421f4'
b=p.LoadBoard(str(ROOT/'a2_usb_uart.kicad_pcb'));old=p.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'))
d=json.loads((OUT/'before/inventory.json').read_text());cs=d['components'];terms=d['terminals'];fps={f.GetReference():f for f in b.GetFootprints()};ofs={f.GetReference():f for f in old.GetFootprints()}
def xy(v):return [round(p.ToMM(v.x),6),round(p.ToMM(v.y),6)]
def canon(n):return n.replace('{slash}','/')
errors=[]
if set(cs)!=set(fps):errors.append('Component-set mismatch')
for ref,c in cs.items():
 f=fps[ref]
 for k,a,z in [('value',f.GetValue(),c['value']),('footprint',f.GetFPID().GetUniStringLibId(),c['footprint']),('DNP',f.IsDNP(),'dnp' in c['properties'])]:
  if a!=z:errors.append([ref,k,a,z])
 for k in ['MPN','Note']:
  if k in c['fields'] and (not f.GetField(k) or f.GetField(k).GetText()!=c['fields'][k]):errors.append([ref,k])
 for pad in f.Pads():
  if canon(pad.GetNetname())!=terms.get(ref+'.'+pad.GetNumber(),''):errors.append([ref,pad.GetNumber(),'net'])
 for terminal in [key.split('.',1)[1] for key in terms if key.startswith(ref+'.')]:
  if not any(a.GetNumber()==terminal for a in f.Pads()):errors.append([ref,terminal,'missing pad'])
# Shape-preserving comparisons use physical geometry and UUID, not serialized order.
def track(t):return {'uuid':t.m_Uuid.AsString(),'start':xy(t.GetStart()),'end':xy(t.GetEnd()),'layer':t.GetLayer(),'width':p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()),'via':isinstance(t,p.PCB_VIA),'drill':p.ToMM(t.GetDrillValue()) if isinstance(t,p.PCB_VIA) else None,'net':t.GetNetname()}
ots={t.m_Uuid.AsString():track(t) for t in old.GetTracks()};nts={t.m_Uuid.AsString():track(t) for t in b.GetTracks()}
kept=set(ots)&set(nts);geometry_changed=[uid for uid in kept if {k:v for k,v in ots[uid].items() if k!='net'}!={k:v for k,v in nts[uid].items() if k!='net'}]
moved={ref:{'before':{'xy':xy(ofs[ref].GetPosition()),'angle':ofs[ref].GetOrientationDegrees()},'after':{'xy':xy(fps[ref].GetPosition()),'angle':fps[ref].GetOrientationDegrees()}} for ref in set(ofs)&set(fps) if xy(ofs[ref].GetPosition())!=xy(fps[ref].GetPosition()) or ofs[ref].GetOrientationDegrees()!=fps[ref].GetOrientationDegrees()}
fixed=['J1','J2','J3','SW1','SW2','SW3']
assert not(set(fixed)&set(moved))
def edges(board):return sorted((g.m_Uuid.AsString(),g.GetShape(),xy(g.GetStart()),xy(g.GetEnd()),g.GetWidth()) for g in board.GetDrawings() if g.GetLayer()==p.Edge_Cuts)
assert edges(old)==edges(b)
def zones(board):
 return sorted((z.m_Uuid.AsString(),z.GetLayer(),[[xy(z.Outline().COutline(i).CPoint(k)) for k in range(z.Outline().COutline(i).PointCount())] for i in range(z.Outline().OutlineCount())],z.GetLocalClearance(),z.GetMinThickness()) for z in board.Zones())
assert zones(old)==zones(b)
assert p.ToMM(b.GetDesignSettings().GetBoardThickness())==1.6 and b.GetCopperLayerCount()==2
edge_points=[pt for g in b.GetDrawings() if g.GetLayer()==p.Edge_Cuts for pt in [xy(g.GetStart()),xy(g.GetEnd())]];outline_size=[round(max(pt[i] for pt in edge_points)-min(pt[i] for pt in edge_points),3) for i in [0,1]]
assert outline_size==[22,50]
assert all(f.GetLayer()==p.F_Cu for f in fps.values())
drc=json.loads((OUT/'after/drc_final.json').read_text());erc=json.loads((OUT/'after/erc_final.json').read_text());before_drc=json.loads((OUT/'before/drc.json').read_text())
assert drc['ignored_checks']==before_drc['ignored_checks'];assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity']
erc_count=sum(len(s.get('violations',[])) for s in erc['sheets']);assert erc_count==0
protected={}
for suffix in ['kicad_sch','kicad_pro']:
 rel='01_New_Design/kicad_direct/a2_usb_uart.'+suffix
 expected=subprocess.check_output(['git','rev-parse',BASE+':'+rel],cwd=REPO,text=True).strip();actual=subprocess.check_output(['git','hash-object','--path='+rel,rel],cwd=REPO,text=True).strip();assert expected==actual;protected[rel]=actual
for rel in ['01_New_Design/kicad_direct/manufacturing_review','01_New_Design/kicad_direct/libraries','01_New_Design/kicad_direct/scripts']:
 assert not subprocess.check_output(['git','diff','--name-only',BASE,'--',rel],cwd=REPO,text=True).strip()
# List visible via-in-pad locations for PCB assembly review (not a DRC waiver).
via_pad=[]
for via in b.GetTracks():
 if not isinstance(via,p.PCB_VIA):continue
 for f in b.GetFootprints():
  for pad in f.Pads():
   if pad.IsOnLayer(p.F_Cu) and pad.GetAttribute()==p.PAD_ATTRIB_SMD and pad.HitTest(via.GetPosition()):via_pad.append({'ref':f.GetReference(),'pad':pad.GetNumber(),'via':via.m_Uuid.AsString(),'pos':xy(via.GetPosition()),'new_via':via.m_Uuid.AsString() not in ots})
usb={}
for name in ['/USB_D+','/USB_D-']:
 usb[name]={}
 for tag,board in [('before',old),('after',b)]:
  ts=[t for t in board.GetTracks() if t.GetNetname()==name];usb[name][tag]={'total_track_mm':round(sum(p.ToMM(t.GetLength()) for t in ts if not isinstance(t,p.PCB_VIA)),4),'vias':sum(isinstance(t,p.PCB_VIA) for t in ts)}
report={'base':BASE,'components':len(cs),'pad_objects':sum(len(list(f.Pads())) for f in fps.values()),'schematic_terminals':len(terms),'errors':errors,'erc':erc_count,'drc':0,'unconnected':0,'schematic_parity':0,'added_components':sorted(set(fps)-set(ofs)),'deleted_components':sorted(set(ofs)-set(fps)),'moved_components':moved,'tracks_before':len(ots),'tracks_after':len(nts),'original_tracks_retained':len(kept),'retained_percent':round(len(kept)/len(ots)*100,2),'original_track_geometry_changes':geometry_changed,'removed_tracks':[ots[k] for k in sorted(set(ots)-set(nts))],'added_tracks':[nts[k] for k in sorted(set(nts)-set(ots))],'protected_io_positions':fixed,'outline_mm':outline_size,'thickness_mm':1.6,'copper_layers':2,'zones_outlines_preserved':True,'all_footprints_front':True,'protected_blobs':protected,'manufacturing_and_libraries_and_original_scripts_unchanged':True,'via_in_smd_pad':via_pad,'usb_total_copper_metrics_not_delay_or_skew':usb,'ignored_checks_unchanged':drc['ignored_checks']}
(OUT/'integrity.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
assert not errors,errors
print(json.dumps({k:v for k,v in report.items() if k not in ['removed_tracks','added_tracks','via_in_smd_pad','ignored_checks_unchanged']},indent=2,ensure_ascii=False))
print('NEW VIA IN SMD PAD',[(q['ref'],q['pad'],q['pos']) for q in via_pad if q['new_via']])
