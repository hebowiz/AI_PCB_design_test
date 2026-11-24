from common import *
import xml.etree.ElementTree as E
from collections import Counter
BASE='5596d3bc8802687b89b21fd9c57e1117ec9382e5';REPO=ROOT.parents[1]
old=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'))
def canon(s):return s.replace('{slash}','/')
def parts(board):
 return {f.GetReference():{'uuid':uid(f),'value':f.GetValue(),'footprint':f.GetFPID().GetUniStringLibId(),'fields':{q.GetName():q.GetText() for q in f.GetFields()},'position':xy(f.GetPosition()),'rotation':f.GetOrientationDegrees(),'layer':f.GetLayer(),'pads':sorted((a.GetNumber(),canon(a.GetNetname()),a.GetShape(),xy(a.GetSize()),xy(a.GetPosition()),a.GetOrientationDegrees(),a.GetAttribute()) for a in f.Pads())} for f in board.GetFootprints()}
assert parts(old)==parts(b),'Attributes, pad nets, shape or placement changed'
xml=E.parse(OUT/'after/schematic.net');comps={q.attrib['ref']:q for q in xml.findall('./components/comp')};terms={}
for net in xml.findall('./nets/net'):
 for node in net.findall('node'):terms[(node.attrib['ref'],node.attrib['pin'])]=canon(net.attrib['name'])
assert set(comps)==set(fps)
for ref,f in fps.items():
 assert f.GetValue()==comps[ref].findtext('value') and f.GetFPID().GetUniStringLibId()==comps[ref].findtext('footprint')
 for p in f.Pads():assert canon(p.GetNetname())==terms.get((ref,p.GetNumber()),'')
def outline(board):return sorted((g.GetShape(),xy(g.GetStart()),xy(g.GetEnd()),g.GetWidth()) for g in board.GetDrawings() if g.GetLayer()==k.Edge_Cuts)
assert outline(old)==outline(b)
assert k.ToMM(b.GetDesignSettings().GetBoardThickness())==1.6 and b.GetCopperLayerCount()==2
for ext in ['kicad_sch','kicad_pro','kicad_dru']:
 assert (ROOT/('a2_usb_uart.'+ext)).read_bytes()==(OUT/'before'/('a2_usb_uart.'+ext)).read_bytes()
 if (OUT/'candidate'/('a2_usb_uart.'+ext)).exists():assert (ROOT/('a2_usb_uart.'+ext)).read_bytes()==(OUT/'candidate'/('a2_usb_uart.'+ext)).read_bytes()
ot={uid(t):record(t) for t in old.GetTracks()};nt={uid(t):record(t) for t in b.GetTracks()};shared=set(ot)&set(nt)
diff={'removed':[ot[q] for q in sorted(set(ot)-set(nt))],'added':[nt[q] for q in sorted(set(nt)-set(ot))],'modified':[{'before':ot[q],'after':nt[q]} for q in sorted(shared) if ot[q]!=nt[q]],'unchanged_count':sum(ot[q]==nt[q] for q in shared)}
(OUT/'copper_diff.json').write_text(json.dumps(diff,indent=2))
priority=['/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT']
assert {u:r for u,r in ot.items() if r['net'] in priority}=={u:r for u,r in nt.items() if r['net'] in priority}
assert all((round(k.ToMM(t.GetDrillValue()),3),round(k.ToMM(t.GetWidth(k.F_Cu)),3))==(.3,.6) for t in b.GetTracks() if isinstance(t,k.PCB_VIA))
assert all(z.GetPadConnection()==k.ZONE_CONNECTION_THERMAL for z in b.Zones() if not z.GetIsRuleArea())
assert '(pad_to_mask_clearance 0.05)' in BOARD.read_text()
for bb in [old,b]:
 assert all(f.GetLocalSolderMaskMargin() is None and f.GetLocalZoneConnection()==-1 for f in bb.GetFootprints())
 assert all(p.GetLocalSolderMaskMargin() is None and p.GetLocalZoneConnection()==-1 for f in bb.GetFootprints() for p in f.Pads())
d=json.loads((OUT/'after/drc_final.json').read_text());assert not d['violations'] and not d['unconnected_items'] and not d['schematic_parity']
e=json.loads((OUT/'after/erc_final.json').read_text());assert not any(s.get('violations') for s in e['sheets'])
source_drc=REPO/'01_New_Design/kicad_direct/reports/pcb_review_batch1/after/drc_final.json';assert d['ignored_checks']==json.loads(source_drc.read_text())['ignored_checks']
assert all(r['ok'] for r in json.loads((OUT/'escape_audit.json').read_text()))
assert not json.loads((OUT/'non45_segments.json').read_text());assert not json.loads((OUT/'grazing_pad_contacts.json').read_text())
assert not json.loads((OUT/'priority_projection_audit.json').read_text())['unexpected_overlaps']
assert all(r['new_loss_over_2um_tolerance_mm2']<.001 for r in json.loads((OUT/'ground_reference_comparison.json').read_text()))
protected={}
for path,sha in [('C:/Users/hebow/.codex/worktrees/a2-pcb-review/99_AI_PCB_design_test/01_New_Design/kicad_direct/a2_usb_uart.kicad_pcb','d55cc3e2146be62a39707161abc60ae3331315a21a19285f17e98840de278c94'),('D:/Documents/KiCad/10.0/projects/99_AI_PCB_design_test/workspaces/A-2/01_New_Design/kicad_direct/a2_usb_uart.kicad_pcb','d55cc3e2146be62a39707161abc60ae3331315a21a19285f17e98840de278c94'),('D:/Documents/KiCad/10.0/projects/99_AI_PCB_design_test/01_New_Design/kicad_direct/a2_usb_uart.kicad_pro','e5b768239d2eb761331199dc0d3ef02ef9c2289797037a22e0de9d5ca595767d')]:
 actual=hashlib.sha256(Path(path).read_bytes()).hexdigest();assert actual==sha;protected[path]=actual
changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=REPO,text=True).splitlines();allowed={'01_New_Design/kicad_direct/a2_usb_uart.kicad_pcb','docs/work_log.md','docs/decision_log.md','docs/discussion_log.md'}
assert all(q in allowed or q.startswith('01_New_Design/kicad_direct/reports/pcb_quality_revision/') for q in changed)
report={'base':BASE,'pcb_sha256':hashlib.sha256(BOARD.read_bytes()).hexdigest(),'components':len(fps),'schematic_terminals':len(terms),'all_attributes_pad_nets_and_positions_identical':True,'schematic_project_custom_rules_byte_identical':True,'outline_mm':[22,50],'outline_identical':True,'thickness_mm':1.6,'layers':2,'priority_copper_uuid_geometry_identical':priority,'erc':0,'drc':0,'unconnected':0,'schematic_parity':0,'same_ignored_checks':d['ignored_checks'],'new_exclusions':0,'via_hole_outer_mm':[.3,.6],'global_mask_clearance_mm':.05,'pad_zone_connection':'thermal','short_edge_crossings':len(json.loads((OUT/'escape_audit.json').read_text())),'short_edge_errors':0,'non45_segments':0,'grazing_contacts':0,'priority_unexpected_underpasses':0,'priority_ground_area_new_loss_mm2':0,'copper_diff_counts':{q:len(v) if isinstance(v,list) else v for q,v in diff.items()},'protected_files':protected}
(OUT/'integrity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
