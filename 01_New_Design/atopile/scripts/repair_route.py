"""Prepare an incremental router pass after KiCad verification of SES import."""
import json, os, sys
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1]
b=k.LoadBoard(str(ROOT/'board/a1.kicad_pcb'))
d=json.loads((ROOT/'reports/drc.json').read_text(encoding='utf-8'))
remove=set()
for v in d['violations']:
    if v['type'] in ['copper_edge_clearance','track_dangling']:
        remove.update(i['uuid'] for i in v['items'])
tracks=list(b.GetTracks());zones=list(b.Zones());deleted=[]
for z in zones:b.Remove(z)
for t in tracks:
    if t.m_Uuid.AsString() in remove and not t.IsLocked():
        deleted.append(dict(net=t.GetNetname(),uuid=t.m_Uuid.AsString()));b.Remove(t)
    else:t.SetLocked(True)
k.SaveBoard(str(ROOT/'board/a1.kicad_pcb'),b)
out=ROOT/'board/repair.dsn';k.ExportSpecctraDSN(b,str(out))
s=out.read_text();s=s.replace('(path pcb 0  22000 -50000  0 -50000  0 0  22000 0  22000 -50000)',
    '(path pcb 0  21850 -49850  150 -49850  150 -150  21850 -150  21850 -49850)')
out.write_text(s)
(ROOT/'reports/route_repair.json').write_text(json.dumps(dict(deleted=deleted,retained_tracks_locked=True,router_boundary_inset_mm=.15),indent=2))
print('Removed',len(deleted),'reported edge/dangling segments; exported repair.dsn')
sys.stdout.flush();os._exit(0)
