from common import *
from collections import defaultdict
import xml.etree.ElementTree as ET
old=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));of={f.GetReference():f for f in old.GetFootprints()}
def xmlnet(path):
 r=ET.parse(path).getroot();comps={c.get('ref'):{x.tag:ET.tostring(x,encoding='unicode').strip() for x in c if x.tag in ['value','footprint','datasheet','fields']} for c in r.find('components')};nets={n.get('name'):sorted(tuple(sorted(x.attrib.items())) for x in n.findall('node')) for n in r.find('nets')};return comps,nets
bc,bn=xmlnet(OUT/'checks/before.net');ac,an=xmlnet(OUT/'checks/after.net');diff=[{'ref':r,'field':key,'before':bc[r].get(key),'after':ac[r].get(key)} for r in bc for key in set(bc[r])|set(ac[r]) if bc[r].get(key)!=ac[r].get(key)]
assert bn==an;assert len(diff)==2 and all(d['ref']=='J3' and d['after']==d['before'].replace('A2:PinHeader_1x04_P2.54mm_Vertical_SMD_Pin1Left','A2:TSM_104_SV') for d in diff);assert set(of)==set(fps)
placements=[];attributes=[];pins=[]
for ref,f in fps.items():
 o=of[ref]
 if xy(o.GetPosition())!=xy(f.GetPosition()) or o.GetOrientationDegrees()!=f.GetOrientationDegrees():placements.append({'ref':ref,'before':[xy(o.GetPosition()),o.GetOrientationDegrees()],'after':[xy(f.GetPosition()),f.GetOrientationDegrees()]})
 if o.GetValue()!=f.GetValue() or {x.GetName():x.GetText() for x in o.GetFields()}!={x.GetName():x.GetText() for x in f.GetFields()}:attributes.append(ref)
 op={p.GetNumber():p for p in o.Pads()}
 for p in f.Pads():
  q=op[p.GetNumber()]
  if q.GetNetname()!=p.GetNetname():pins.append([ref,p.GetNumber(),q.GetNetname(),p.GetNetname()])
assert not attributes and not pins
before={uid(t):record(t) for t in old.GetTracks()};after={uid(t):record(t) for t in b.GetTracks()}
removed=[before[i] for i in before.keys()-after.keys()];added=[after[i] for i in after.keys()-before.keys()];edited=[{'before':before[i],'after':after[i]} for i in before.keys()&after.keys() if before[i]!=after[i]]
priority=['/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT'];assert not any(r['net'] in priority for r in removed+added);assert not any(r['before']['net'] in priority for r in edited)
def totals(board):
 d=defaultdict(float)
 for t in board.GetTracks():
  if not isinstance(t,k.PCB_VIA):d[t.GetNetname()]+=k.ToMM(t.GetLength())
 return dict(d)
bl,al=totals(old),totals(b);lengths=[{'net':n,'before_mm':round(bl.get(n,0),4),'after_mm':round(al.get(n,0),4),'delta_mm':round(al.get(n,0)-bl.get(n,0),4)} for n in sorted(set(bl)|set(al))]
(OUT/'copper_diff.json').write_text(json.dumps({'removed':removed,'added':added,'edited':edited},indent=2));(OUT/'net_lengths.json').write_text(json.dumps(lengths,indent=2))
points=[xy(get()) for g in b.GetDrawings() if g.GetLayer()==k.Edge_Cuts for get in [g.GetStart,g.GetEnd]];edge={'x_min':min(q[0] for q in points),'x_max':max(q[0] for q in points),'y_min':min(q[1] for q in points),'y_max':max(q[1] for q in points)}
result={'base_commit':'cd67233358d06e299d319934ea59fc6a67662b57','real_components':len(fps),'component_attributes_equal':not attributes,'pcb_pin_net_equal':not pins,'schematic_pin_function_type_and_net_equal':bn==an,'expected_footprint_change':diff,'placements':placements,'priority_routing_unchanged':True,'board':edge,'thickness_mm':k.ToMM(b.GetDesignSettings().GetBoardThickness()),'copper_layers':b.GetCopperLayerCount(),'copper_diff_counts':{'removed':len(removed),'added':len(added),'edited':len(edited)},'total_length_mm':[sum(bl.values()),sum(al.values())],'counts_before_after':[[len(list(old.GetTracks())),len(list(old.Zones()))],[len(list(b.GetTracks())),len(list(b.Zones()))]],'project_and_rules_unchanged':{s:hashlib.sha256((ROOT/('a2_usb_uart.'+s)).read_bytes()).hexdigest()==hashlib.sha256((OUT/'before'/('a2_usb_uart.'+s)).read_bytes()).hexdigest() for s in ['kicad_pro','kicad_dru']}}
(OUT/'integrity.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
