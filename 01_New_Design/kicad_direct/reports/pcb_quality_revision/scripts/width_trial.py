from common import *
snapshot=BOARD.read_bytes();log=[]
try:
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA) or 'USB5V' not in t.GetNetname():continue
  w=.5
  if t.GetNetname()=='USB5V' and min(math.dist(xy(t.GetStart()),xy(pad('U1',40).GetPosition())),math.dist(xy(t.GetEnd()),xy(pad('U1',40).GetPosition())))<.75:w=.25
  log.append(record(t));t.SetWidth(k.FromMM(w))
 r=drc('width_trial');(OUT/'checks/width_trial.kicad_pcb').write_bytes(BOARD.read_bytes());(OUT/'width_trial_segments.json').write_text(json.dumps(log,indent=2),encoding='utf-8')
 from collections import Counter
 print(Counter(e['type'] for e in r['violations']))
 for e in r['violations'][:20]:print(e['type'],e['description'],[(i['description'],i['uuid']) for i in e['items']],flush=True)
finally:BOARD.write_bytes(snapshot)
