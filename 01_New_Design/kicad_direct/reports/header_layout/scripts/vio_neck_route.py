from local_router import *
backup=BOARD.read_bytes();ids={r['uuid'] for r in json.loads((OUT/'vio_shortcut_plan.json').read_text())}|{'afbf2a6d-dfb7-4274-ae19-38464af68722','a61461ee-4305-4837-83dc-02def9448d2b'}
orig=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));assert not ids.intersection(uid(t) for t in orig.GetTracks())
for t in list(b.GetTracks()):
 if uid(t) in ids:remove(t)
a=(106.1,133);c=(112.2,132.4);rr=route(a,c,'VIO',.15,(),[a,c],1,0)
if not rr:print('No shorter path; unchanged');raise SystemExit(0)
length=sum(k.ToMM(t.GetLength()) for t in rr if not isinstance(t,k.PCB_VIA));print('replacement_length',length)
if length>=48:print('Rejected long route; unchanged');raise SystemExit(0)
r=drc('vio_shortcut')
if r['violations'] or r['unconnected_items']:BOARD.write_bytes(backup);print('Restored because verification failed')
else:(OUT/'vio_shortcut_result.json').write_text(json.dumps({'before_mm':48.649,'after_mm':length,'new':[record(t) for t in rr]},indent=2))
