"""Read-only comparison of final PCB with the reviewed baseline and unchanged schematic."""
from common import *
from collections import Counter
import hashlib,xml.etree.ElementTree as E
BASE='a300e1c7cd89654fd2800c1bc7b8bad59dae5516';REPO=ROOT.parents[1]
old=p.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));oldfps={f.GetReference():f for f in old.GetFootprints()};errors=[]
def canon(s):return s.replace('{slash}','/')
def parts(board):
 return {f.GetReference():{'uuid':f.m_Uuid.AsString(),'value':f.GetValue(),'footprint':f.GetFPID().GetUniStringLibId(),'fields':{q.GetName():q.GetText() for q in f.GetFields()},'pads':sorted((a.GetNumber(),canon(a.GetNetname()),a.GetShape(),xy(a.GetSize()),a.GetAttribute()) for a in f.Pads())} for f in board.GetFootprints()}
a,c=parts(old),parts(b)
assert a==c,'Component attributes / terminal nets changed'
xml=E.parse(OUT/'after/schematic.net');comps={q.attrib['ref']:q for q in xml.findall('./components/comp')};terms={}
for net in xml.findall('./nets/net'):
 for node in net.findall('node'):terms[(node.attrib['ref'],node.attrib['pin'])]=canon(net.attrib['name'])
assert set(comps)==set(fps)
for ref,f in fps.items():
 q=comps[ref];assert f.GetValue()==q.findtext('value');assert f.GetFPID().GetUniStringLibId()==q.findtext('footprint')
 for pad in f.Pads():assert canon(pad.GetNetname())==terms.get((ref,pad.GetNumber()),'')
def shape(board):return sorted((g.GetShape(),xy(g.GetStart()),xy(g.GetEnd()),g.GetWidth()) for g in board.GetDrawings() if g.GetLayer()==p.Edge_Cuts)
assert shape(old)==shape(b)
fixed=['J1','J2','J3','SW1','SW2','SW3'];assert all(xy(oldfps[r].GetPosition())==xy(fps[r].GetPosition()) and oldfps[r].GetOrientationDegrees()==fps[r].GetOrientationDegrees() for r in fixed)
assert p.ToMM(b.GetDesignSettings().GetBoardThickness())==1.6 and b.GetCopperLayerCount()==2
moved={r:{'before':[ *xy(oldfps[r].GetPosition()),oldfps[r].GetOrientationDegrees()],'after':[ *xy(fps[r].GetPosition()),fps[r].GetOrientationDegrees()]} for r in fps if xy(oldfps[r].GetPosition())!=xy(fps[r].GetPosition()) or oldfps[r].GetOrientationDegrees()!=fps[r].GetOrientationDegrees()}
def record(t):return {'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'layer':t.GetLayer(),'a':xy(t.GetStart()),'b':xy(t.GetEnd()),'width':p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()),'via':isinstance(t,p.PCB_VIA),'hole':p.ToMM(t.GetDrillValue()) if isinstance(t,p.PCB_VIA) else None}
ot={t.m_Uuid.AsString():record(t) for t in old.GetTracks()};nt={t.m_Uuid.AsString():record(t) for t in b.GetTracks()};common=set(ot)&set(nt)
copper={'removed':[ot[q] for q in sorted(set(ot)-set(nt))],'added':[nt[q] for q in sorted(set(nt)-set(ot))],'modified':[{'before':ot[q],'after':nt[q]} for q in sorted(common) if ot[q]!=nt[q]],'unchanged_count':sum(ot[q]==nt[q] for q in common)}
(OUT/'copper_diff.json').write_text(json.dumps(copper,indent=2));protected={}
paths=['a2_usb_uart.kicad_sch','libraries','scripts','manufacturing_review']
for path in paths:
 rel='01_New_Design/kicad_direct/'+path;diff=subprocess.check_output(['git','diff','--name-only',BASE,'--',rel],cwd=REPO,text=True).strip();assert not diff;protected[rel]='unchanged'
pro_before=json.loads((OUT/'before/a2_usb_uart.kicad_pro').read_text());pro_after=json.loads((ROOT/'a2_usb_uart.kicad_pro').read_text());assert pro_before['board']['design_settings']['drc_exclusions']==pro_after['board']['design_settings']['drc_exclusions'];assert pro_before['board']['design_settings']['rule_severities']==pro_after['board']['design_settings']['rule_severities']
d=json.loads((OUT/'after/drc_final.json').read_text());assert not d['violations'] and not d['unconnected_items'] and not d['schematic_parity'];erc=json.loads((OUT/'after/erc_final.json').read_text());assert not any(s.get('violations') for s in erc['sheets']);assert d['ignored_checks']==json.loads((OUT/'before/drc.json').read_text())['ignored_checks']
via_dims=Counter((round(p.ToMM(t.GetDrillValue()),4),round(p.ToMM(t.GetWidth(p.F_Cu)),4)) for t in b.GetTracks() if isinstance(t,p.PCB_VIA));assert set(via_dims)=={(.3,.6)}
escapes=json.loads((OUT/'escape_audit.json').read_text());assert all(q['ok'] for q in escapes);assert not json.loads((OUT/'grazing_pad_contacts.json').read_text());assert not json.loads((OUT/'non45_segments.json').read_text())
capmap={'C1':('U1',40),'C23':('U1',40),'C2':('U1',39),'C5':('U1',39),'C3':('U1',12),'C4':('U1',24),'C6':('U1',46),'C7':('U1',37),'C8':('U1',38),'C9':('U1',3),'C10':('U1',8),'C15':('U5',8),'C16':('U2',1),'C17':('U2',16),'C18':('U4',1),'C19':('U4',5)}
distances={r:{tag:round(math.dist(xy(fs[r].GetPosition()),xy(next(a for a in fs[ic].Pads() if a.GetNumber()==str(n)).GetPosition())),3) for tag,fs in [('before',oldfps),('after',fps)]} for r,(ic,n) in capmap.items()}
metrics={}
for net in ['/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT']:
 metrics[net]={tag:{'total_track_mm':round(sum(p.ToMM(t.GetLength()) for t in bb.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname()==net),4),'vias':sum(isinstance(t,p.PCB_VIA) and t.GetNetname()==net for t in bb.GetTracks())} for tag,bb in [('before',old),('after',b)]}
counts={tag:{'segments':sum(not isinstance(t,p.PCB_VIA) for t in bb.GetTracks()),'shorter_than_0_3_mm':sum(not isinstance(t,p.PCB_VIA) and p.ToMM(t.GetLength())<.3 for t in bb.GetTracks()),'vias':sum(isinstance(t,p.PCB_VIA) for t in bb.GetTracks())} for tag,bb in [('before',old),('after',b)]}
assert '(pad_to_mask_clearance 0.05)' in (ROOT/'a2_usb_uart.kicad_pcb').read_text()
assert all(a.GetLocalSolderMaskMargin() is None and a.GetLocalZoneConnection()==-1 for f in b.GetFootprints() for a in f.Pads())
assert all(f.GetLocalSolderMaskMargin() is None and f.GetLocalZoneConnection()==-1 for f in b.GetFootprints())
assert all(z.GetPadConnection()==p.ZONE_CONNECTION_THERMAL for z in b.Zones() if not z.GetIsRuleArea())
assert not json.loads((OUT/'priority_projection_audit.json').read_text())['unexpected_overlaps']
report={'global_mask_expansion_mm':0.05,'pad_and_footprint_mask_overrides':False,'ground_zones_pad_connection':'thermal','priority_unexpected_projection_overlaps':0,'base':BASE,'components':len(fps),'schematic_terminals':len(terms),'attributes_and_pin_net_map_identical':True,'erc':0,'drc':0,'unconnected':0,'schematic_parity':0,'drc_exclusions_and_severities_unchanged':True,'ignored_checks':d['ignored_checks'],'fixed_positions':fixed,'outline_unchanged':True,'outline_mm':[22,50],'thickness_mm':1.6,'layers':2,'moved_components':moved,'track_counts':counts,'copper_diff_counts':{k:len(v) if isinstance(v,list) else v for k,v in copper.items()},'via_dimensions':{'hole_0_3_outer_0_6_count':sum(via_dims.values())},'short_edge_crossings':len(escapes),'short_edge_deviations':0,'grazing_contacts':0,'non45_segments':0,'cap_to_pin_distances_mm':distances,'signal_copper_lengths_including_branches_not_electrical_skew':metrics,'protected':protected}
(OUT/'integrity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['moved_components','ignored_checks','cap_to_pin_distances_mm']},ensure_ascii=False,indent=2))
