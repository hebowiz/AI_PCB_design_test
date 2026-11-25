from local_router import *
ids={r['uuid'] for r in json.loads((OUT/'r12_tail_replacement.json').read_text())};original=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));assert not ids.intersection(uid(t) for t in original.GetTracks());assert len(ids)==21
for t in list(b.GetTracks()):
 if uid(t) in ids:remove(t)
fps['R12'].SetPosition(v(116.1,135.85));fps['R12'].Reference().SetPosition(v(116.1,135.1))
import local_router as lr
lr.PADGEOM[:]=[(p,poly(p)) for f in fps.values() for p in f.Pads()]
for n in ['1','2']:
 p=pad('R12',n);track(xy(p.GetPosition()),(114.9 if n=='1' else 117.05,135.85),p.GetNetname(),w=.15)
for n,end,z in [('2',(114.25,131.95),1),('1',(115.5,132.01),0)]:
 p=pad('R12',n);q=xy(p.GetPosition());a=(114.9 if n=='1' else 117.05,135.85)
 assert route(a,end,p.GetNetname(),.15,['R12.'+n],[a,end],0,z)
drc('r12_reconnected')
