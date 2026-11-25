from local_router import *
backup=BOARD.read_bytes();ids={r['uuid'] for r in json.loads((OUT/'vio_shortcut_plan.json').read_text())}|{'afbf2a6d-dfb7-4274-ae19-38464af68722','a61461ee-4305-4837-83dc-02def9448d2b','5fc1d11e-5cf7-4548-b552-1342805a7ed7','fc281d96-b43c-4ced-9961-ff020e143e92'}
for t in list(b.GetTracks()):
 if uid(t) in ids:remove(t)
fps['C19'].SetOrientationDegrees(180);fps['C19'].Reference().SetPosition(v(108.4,134.3))
import local_router as lr
lr.PADGEOM[:]=[(p,poly(p)) for f in fps.values() for p in f.Pads()]
a=xy(pad('C19',1).GetPosition());c=(112.2,132.4);rr=route(a,c,'VIO',.3,['C19.1'],[a,c,(106.1,133)],0,0)
if rr:
 rr2=route((106.1,133),a,'VIO',.3,['C19.1'],[a,c,(106.1,133)],1,0)
 if rr2:rr+=rr2
 else:rr=None
if not rr:raise SystemExit('No path; unchanged')
length=sum(k.ToMM(t.GetLength()) for t in rr if not isinstance(t,k.PCB_VIA));print('replacement_length',length)
if length>=35:raise SystemExit('Rejected long path; unchanged')
r=drc('vio_compact')
if r['violations'] or r['unconnected_items']:BOARD.write_bytes(backup);print('Restored; verification failed')
else:(OUT/'vio_shortcut_result.json').write_text(json.dumps({'before_mm':48.649,'after_mm':length,'C19_rotation':180,'new':[record(t) for t in rr]},indent=2))
