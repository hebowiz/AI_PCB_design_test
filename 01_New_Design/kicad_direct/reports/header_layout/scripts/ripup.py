from common import *
import collections
plan=json.loads((OUT/'placement_plan.json').read_text());moved=set(plan['after'])
ids={x['uuid'] for x in plan['copper_candidates'] if x['net']!='/USB5V_SW'}
for t in b.GetTracks():
 if t.GetNetname() in ['/FB','/FB_3V3'] or (t.GetNetname()=='/PWR_EN' and max(xy(t.GetStart())[1],xy(t.GetEnd())[1])>=132):ids.add(uid(t))
# Explicit DRC evidence identifies additional copper under relocated pads.
r=json.loads((OUT/'checks/placement.json').read_text());padids={p.m_Uuid.AsString() for ref in moved for p in fps[ref].Pads()}
for x in r['violations']:
 if x['type'] not in ['clearance','shorting_items','hole_clearance']:continue
 if any(i['uuid'] in padids for i in x['items']):
  ids.update(i['uuid'] for i in x['items'] if any(uid(t)==i['uuid'] for t in b.GetTracks()))
ids.update(['88928ffa-d060-4bf7-8953-5765164e6d9b','7805ef04-c623-4c99-a9ea-73c1bb76b243'])
ids.update(['110b147e-ad36-4f34-8516-090a56259323','5b08eee4-3750-4d46-be55-5cf7b2990c9a'])
old=[record(t) for t in b.GetTracks() if uid(t) in ids]
assert all(min(t['a'][1],t['b'][1])>124 for t in old)
assert all(t['net'] not in ['/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT'] for t in old)
(OUT/'replacement_plan.json').write_text(json.dumps({'reason':'Approved R-0034 local J2/J3 and power placement update; evidence placement.json','selected_copper':old},indent=2))
for t in list(b.GetTracks()):
 if uid(t) in ids:remove(t)
print('Local replacement',len(old),dict(collections.Counter(t['net'] for t in old)))
drc('ripup')
