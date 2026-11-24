from common import *
from collections import Counter
j=drc('replacement_plan');lookup={t.m_Uuid.AsString():t for t in b.GetTracks()};protected={'/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT'};rows={}
for e in j['violations']:
 if e['type'] not in ['clearance','shorting_items','tracks_crossing','hole_clearance','track_dangling','via_dangling']:continue
 for a in e['items']:
  t=lookup.get(a['uuid'])
  if t is None or t.GetNetname() in protected:continue
  k=t.m_Uuid.AsString()
  if k not in rows:rows[k]={'uuid':k,'net':t.GetNetname(),'kind':'via' if isinstance(t,p.PCB_VIA) else 'track','start':xy(t.GetStart()),'end':xy(t.GetEnd()),'layer':b.GetLayerName(t.GetLayer()),'reasons':[]}
  rows[k]['reasons'].append(e['type'])
result={'mode':'PLAN ONLY - no copper removed','base':'a300e1c7cd89654fd2800c1bc7b8bad59dae5516','candidate_items':list(rows.values()),'counts':dict(Counter(q['kind'] for q in rows.values())),'protected':['schematic','component identities and nets','outline','J1/J2/J3/SW1/SW2/SW3 placement','USB/crystal priority routes'],'procedure':'Replace selected conflicting fanout/via copper locally; connect approved schematic terminals; report retained/removed/added UUIDs; ERC/DRC/net parity mandatory. No global board generator.'}
(OUT/'replacement_plan.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(result['counts']);print(Counter(q['net'] for q in rows.values()))
