from common import *
base=OUT/'before';assert hashlib.sha256(BOARD.read_bytes()).hexdigest()=='d55cc3e2146be62a39707161abc60ae3331315a21a19285f17e98840de278c94'
scope=json.loads((base/'proposed_scope.json').read_text());allowed={r['net'] for r in scope if not r['tier'].startswith('P')}
ids=set()
for r in json.loads((base/'cycles.json').read_text()):
 if r['net'] in allowed:ids.update(r['uuids'])
for r in json.loads((base/'leaf_assessment.json').read_text()):
 if r['net'] in allowed:ids.update(r['uuids'])
for r in json.loads((base/'duplicate_overlap.json').read_text()):
 if r['net'] in allowed:ids.update(r['uuids'])
candidates=[t for t in b.GetTracks() if uid(t) in ids and t.GetNetname() in allowed and not isinstance(t,k.PCB_VIA)]
(OUT/'redundancy_plan.json').write_text(json.dumps([record(t) for t in candidates],indent=2),encoding='utf-8')
assert count()==0;log=[]
for net in sorted(allowed):
 removed=[]
 for t in sorted([t for t in candidates if t.GetNetname()==net],key=lambda t:-t.GetLength()):
  rec=record(t);remove(t)
  if count()==0:rec['reason']='candidate redundancy; native terminal connectivity preserved';removed.append(rec)
  else:b.Add(t);count()
 if removed:
  log.extend(removed);print(net,'removed',len(removed),'unconnected',count(),flush=True)
# Keep vias for routing decisions; no wholesale via deletion.
(OUT/'redundancy_removed.json').write_text(json.dumps(log,indent=2),encoding='utf-8')
r=drc('redundancy');print('removed total',len(log),flush=True)
