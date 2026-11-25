from local_router import *
backup=BOARD.read_bytes();ids={r['uuid'] for r in json.loads((OUT/'vio_shortcut_plan.json').read_text())}|{'afbf2a6d-dfb7-4274-ae19-38464af68722','a61461ee-4305-4837-83dc-02def9448d2b'}
for t in list(b.GetTracks()):
 if uid(t) in ids:remove(t)
old=[(xy(p.GetPosition()),p) for p in fps['C19'].Pads()];fps['C19'].SetPosition(v(108,133.5));fps['C19'].Reference().SetPosition(v(108.4,134.7))
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):continue
 for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  p=next((p for q,p in old if math.dist(q,xy(get()))<.0001),None)
  if p:setter(p.GetPosition())
import local_router as lr
lr.PADGEOM[:]=[(p,poly(p)) for f in fps.values() for p in f.Pads()]
a=xy(pad('C19',1).GetPosition());c=(112.2,132.4);rr=route(a,c,'VIO',.3,['C19.1'],[a,c,(106.1,133)],0,0)
if not rr:raise SystemExit('No path; unchanged')
length=sum(k.ToMM(t.GetLength()) for t in rr if not isinstance(t,k.PCB_VIA));print('replacement_length',length)
if length>=35:raise SystemExit('Rejected long path; unchanged')
r=drc('vio_compact')
if r['violations'] or r['unconnected_items']:BOARD.write_bytes(backup);print('Restored; verification failed')
else:(OUT/'vio_shortcut_result.json').write_text(json.dumps({'before_mm':48.649,'after_mm':length,'C19_shift_mm':[0,.5],'new':[record(t) for t in rr]},indent=2))
