"""Apply only approved replacement-plan UUIDs that conflict; preserve new priority/power work."""
from common import *
plan=json.loads((OUT/'replacement_plan.json').read_text());allowed={a['uuid'] for a in plan['candidate_items']};fan=json.loads((OUT/'fanouts.json').read_text());logs=[]
def protected(t):
 if t.GetNetname() in ['/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT']:return True
 if isinstance(t,p.PCB_VIA):return False
 return any(math.dist(xy(t.GetEnd()),q)<.0001 or math.dist(xy(t.GetStart()),q)<.0001 for q in fan.values()) and p.ToMM(t.GetLength())<1.2
for i in range(5):
 d=drc('cleanup'+str(i));lookup={t.m_Uuid.AsString():t for t in b.GetTracks()};remove_ids=set();unresolved=[]
 for e in d['violations']:
  if e['type'] not in ['clearance','shorting_items','tracks_crossing','hole_clearance','track_dangling','via_dangling']:continue
  ts=[lookup[a['uuid']] for a in e['items'] if a['uuid'] in lookup and a['uuid'] in allowed];ts=[t for t in ts if not protected(t)]
  if not ts:unresolved.append(e);continue
  ts.sort(key=lambda t:(not isinstance(t,p.PCB_VIA),p.ToMM(t.GetLength())))
  remove_ids.add(ts[0].m_Uuid.AsString())
 for uid in remove_ids:remove(lookup[uid])
 logs.append({'pass':i,'removed':sorted(remove_ids),'unresolved':unresolved});print('pass',i,'removed',len(remove_ids),'outside this plan',len(unresolved),flush=True)
 if not remove_ids:break
save(True);(OUT/'conflict_cleanup.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2))
