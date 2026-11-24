from common import *
import xml.etree.ElementTree as E
old=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));of={f.GetReference():f for f in old.GetFootprints()};canon=lambda s:s.replace('{slash}','/')
def props(f):
 return {'uuid':uid(f),'value':f.GetValue(),'footprint':f.GetFPID().GetUniStringLibId(),'fields':{q.GetName():q.GetText() for q in f.GetFields()},'attributes':f.GetAttributes(),'pads':sorted((p.GetNumber(),canon(p.GetNetname()),p.GetShape(),xy(p.GetSize()),p.GetAttribute()) for p in f.Pads())}
assert set(of)==set(fps)
assert {r:props(f) for r,f in of.items()}=={r:props(f) for r,f in fps.items()}
moved=[]
for r,f in fps.items():
 a=of[r];p0=[xy(a.GetPosition()),a.GetOrientationDegrees(),a.GetLayer()];p1=[xy(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer()]
 if p0!=p1:moved.append({'ref':r,'before':p0,'after':p1})
assert {r['ref'] for r in moved}=={'FB1','FB2','C1','C2','C3','C10','C11','C12','R1'}
xml=E.parse(OUT/'after/schematic.net');comps={q.attrib['ref']:q for q in xml.findall('./components/comp')};terms={}
for n in xml.findall('./nets/net'):
 for q in n.findall('node'):terms[(q.attrib['ref'],q.attrib['pin'])]=canon(n.attrib['name'])
assert set(comps)==set(fps)
for r,f in fps.items():
 assert f.GetValue()==comps[r].findtext('value') and f.GetFPID().GetUniStringLibId()==comps[r].findtext('footprint')
 for p in f.Pads():assert canon(p.GetNetname())==terms.get((r,p.GetNumber()),'')
for ext in ['kicad_sch','kicad_pro','kicad_dru']:
 assert (ROOT/('a2_usb_uart.'+ext)).read_bytes()==(OUT/'before'/('a2_usb_uart.'+ext)).read_bytes()==(OUT/'candidate'/('a2_usb_uart.'+ext)).read_bytes()
def outline(bb):return sorted((g.GetShape(),xy(g.GetStart()),xy(g.GetEnd()),g.GetWidth()) for g in bb.GetDrawings() if g.GetLayer()==k.Edge_Cuts)
assert outline(b)==outline(old) and k.ToMM(b.GetDesignSettings().GetBoardThickness())==1.6 and b.GetCopperLayerCount()==2
ots={uid(t):record(t) for t in old.GetTracks()};nts={uid(t):record(t) for t in b.GetTracks()};shared=set(ots)&set(nts)
diff={'removed':[ots[u] for u in sorted(set(ots)-set(nts))],'added':[nts[u] for u in sorted(set(nts)-set(ots))],'modified':[{'before':ots[u],'after':nts[u]} for u in sorted(shared) if ots[u]!=nts[u]],'unchanged_count':sum(ots[u]==nts[u] for u in shared)}
(OUT/'copper_diff.json').write_text(json.dumps(diff,indent=2))
assert {u:r for u,r in ots.items() if r['net'] in ['/USB_D+','/USB_D-']}=={u:r for u,r in nts.items() if r['net'] in ['/USB_D+','/USB_D-']}
assert all((round(k.ToMM(t.GetDrillValue()),3),round(k.ToMM(t.GetWidth(k.F_Cu)),3))==(.3,.6) for t in b.GetTracks() if isinstance(t,k.PCB_VIA))
assert all(z.GetPadConnection()==k.ZONE_CONNECTION_THERMAL for z in b.Zones() if not z.GetIsRuleArea())
assert '(pad_to_mask_clearance 0.05)' in BOARD.read_text()
d=json.loads((OUT/'after/drc_final.json').read_text());e=json.loads((OUT/'after/erc_final.json').read_text())
assert not d['violations'] and not d['unconnected_items'] and not d['schematic_parity']
assert not any(s.get('violations') for s in e['sheets'])
assert d['ignored_checks']==json.loads((ROOT/'reports/pcb_quality_revision/after/drc_final.json').read_text())['ignored_checks']
assert all(r['ok'] for r in json.loads((OUT/'escape_audit.json').read_text()))
assert not json.loads((OUT/'non45_segments.json').read_text()) and not json.loads((OUT/'grazing_pad_contacts.json').read_text())
assert not json.loads((OUT/'priority_projection_audit.json').read_text())['unexpected_overlaps']
assert all(r['new_loss_over_2um_tolerance_mm2']<.001 for r in json.loads((OUT/'ground_reference_comparison.json').read_text()))
assert all(r['in_order'] for r in json.loads((OUT/'after/analysis/power_order.json').read_text()))
rr=json.loads((OUT/'all_turns.json').read_text());corners=[r for r in rr if r['degree']==2 and not r['pins'] and not r['vias']];assert not corners
protected={}
for path,sha in [('C:/Users/hebow/.codex/worktrees/a2-pcb-review/99_AI_PCB_design_test/01_New_Design/kicad_direct/a2_usb_uart.kicad_pcb','d55cc3e2146be62a39707161abc60ae3331315a21a19285f17e98840de278c94'),('D:/Documents/KiCad/10.0/projects/99_AI_PCB_design_test/01_New_Design/kicad_direct/a2_usb_uart.kicad_pro','e5b768239d2eb761331199dc0d3ef02ef9c2289797037a22e0de9d5ca595767d')]:
 actual=hashlib.sha256(Path(path).read_bytes()).hexdigest();assert actual==sha;protected[path]=actual
r={'base':'87711e88e10653e79fdce9c3ade341b8f1440489','pcb_sha256':hashlib.sha256(BOARD.read_bytes()).hexdigest(),'components':len(fps),'schematic_terminals':len(terms),'attributes_footprints_pad_nets_identical':True,'moved_footprints':moved,'schematic_project_rules_byte_identical':True,'outline_mm':[22,50],'thickness_mm':1.6,'layers':2,'usb_copper_uuid_geometry_identical':True,'erc':0,'drc':0,'unconnected':0,'schematic_parity':0,'new_exclusions':0,'via_hole_outer_mm':[.3,.6],'global_mask_clearance_mm':.05,'pad_zone_connection':'thermal','short_edge_crossings':len(json.loads((OUT/'escape_audit.json').read_text())),'short_edge_errors':0,'non45_segments':0,'grazing_contacts':0,'ordinary_ge90_corners':0,'raw_turn_candidates':rr,'power_chains_verified':10,'copper_diff_counts':{q:len(vv) if isinstance(vv,list) else vv for q,vv in diff.items()},'protected_files':protected}
(OUT/'integrity.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False,indent=2))
