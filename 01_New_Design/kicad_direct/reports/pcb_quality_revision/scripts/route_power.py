from local_router import *
from ground import stitch_ground
assert BOARD.parent==OUT.resolve()/"candidate", "Power rerouting is restricted to a candidate file"
net=sys.argv[1];tag=net.replace('/','').lower();snapshot=BOARD.read_bytes();original=[t for t in b.GetTracks() if t.GetNetname()==net]
(OUT/(tag+'_replacement_plan.json')).write_text(json.dumps([record(t) for t in original],indent=2),encoding='utf-8')
for t in original:remove(t)
log=[];ok=False
try:
 if net=='/USB5V_SW':
  q=xy(pad('SW2',2).GetPosition());portal=(105.1,q[1]);track(q,portal,net,w=.5)
  jobs=[(portal,xy(pad('TP1',1).GetPosition()),['TP1.1'],[portal]),(xy(pad('R17',1).GetPosition()),xy(pad('TP1',1).GetPosition()),['R17.1','TP1.1'],[xy(pad('TP1',1).GetPosition())])]
 elif net=='USB5V_OUT':
  q=xy(pad('J2',4).GetPosition());portal=(q[0],145.4);track(q,portal,net,w=.5)
  jobs=[(portal,xy(pad('TP2',1).GetPosition()),['TP2.1'],[portal]),(xy(pad('R17',2).GetPosition()),xy(pad('TP2',1).GetPosition()),['R17.2','TP2.1'],[xy(pad('TP2',1).GetPosition())])]
 elif net=='USB5V':
  # Retain the existing C18-to-U4 straight connection UUID, widen to .5.
  kept=next(t for t in original if uid(t)=='690afe98-279c-4f5b-b7f1-554a1b34df13');b.Add(kept);kept.SetWidth(k.FromMM(.5))
  kept2=next(t for t in original if uid(t)=='9a0c0b66-236f-4f70-8a21-bd5c76a20ed9');b.Add(kept2);kept2.SetWidth(k.FromMM(.25));kept2.SetEnd(v(116.3,117.25))
  q=xy(pad('SW2',3).GetPosition());sw=(105.1,q[1]);track(q,sw,net,w=.5)
  j=xy(pad('J1',1).GetPosition());jp=(107.5,103.25);track(j,jp,net,w=.5)
  c1=xy(pad('C1',1).GetPosition());c18=xy(pad('C18',1).GetPosition());c23=xy(pad('C23',1).GetPosition())
  jobs=[(jp,c1,['C1.1'],[jp]),(c23,c1,['C23.1','C1.1'],[c1]),((116.3,117.25),c23,['C23.1','U1.40'],[(116.3,117.25),c23]),(c18,c1,['C18.1','C1.1'],[c18,c1]),(sw,c18,['C18.1'],[sw,c18]),(xy(pad('R13',1).GetPosition()),jp,['R13.1'],[jp])]
 else:raise ValueError(net)
 for a,c,pins,junctions in jobs:
  rr=route(a,c,net,.5,pins,junctions)
  if rr is None:raise RuntimeError('routing failed; working PCB remains unchanged')
  log.append({'from':a,'to':c,'new':[record(t) for t in rr]})
 stitches=stitch_ground();(OUT/(tag+'_ground_stitches.json')).write_text(json.dumps(stitches,indent=2),encoding='utf-8')
 result=drc(tag);(OUT/(tag+'_routing.json')).write_text(json.dumps(log,indent=2),encoding='utf-8')
 if result['violations'] or result['unconnected_items']:raise RuntimeError('candidate does not pass all DRC/connectivity checks; restoring previous candidate')
 ok=True
finally:
 if not ok:
  if BOARD.read_bytes()!=snapshot:(OUT/'checks'/(tag+'_failed.kicad_pcb')).write_bytes(BOARD.read_bytes());BOARD.write_bytes(snapshot)
 sys.stdout.flush();sys.stderr.flush()
