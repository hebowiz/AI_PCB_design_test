from common import *
import xml.etree.ElementTree as ET
assert (ROOT/'a2_usb_uart.kicad_pcb').read_bytes()==BOARD.read_bytes()
f=fps['J1'];loc=[xy(p.GetPosition()) for p in f.Pads() if p.GetAttribute()==k.PAD_ATTRIB_NPTH];assert len(loc)==2 and all(p[1]==102.75 for p in loc)
assert all(xy(p.GetPosition())[1]==105.35 for p in f.Pads() if p.GetNumber() in ['1','2','3','4'])
def net(path):
 r=ET.parse(path).getroot()
 return {key:ET.tostring(r.find(key),encoding='unicode') for key in ['components','libparts','libraries','nets']}
# Library paths differ in isolated export locations; compare identities/fields and terminal lists.
a,c=net(OUT/'checks/before.net'),net(OUT/'checks/after.net')
for key in ['components','libparts','nets']:assert a[key]==c[key],key
q0=json.loads((OUT/'checks/quality_before/summary.json').read_text());q1=json.loads((OUT/'checks/quality_after/summary.json').read_text())
keys=['turn_ge90','detour_pairs','independent_cycles','non_GND_cycles','leaf_candidates','non_GND_leaf_candidates','duplicate_overlap_pairs','near_pad_track_pairs','corridor_track_pair_hits']
report={'pcb_on_disk_matches_verified_candidate':True,'component_libpart_terminal_netlist_equal':True,'drc':json.loads((OUT/'checks/final_drc.json').read_text())['violations'],'erc':[v for s in json.loads((OUT/'checks/final_erc.json').read_text())['sheets'] for v in s['violations']],'quality_before_after':{key:[q0[key],q1[key]] for key in keys},'pcb_sha256':hashlib.sha256(BOARD.read_bytes()).hexdigest(),'real_j1_locator_coordinates_mm':loc}
(OUT/'checks/final_summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

