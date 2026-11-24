"""Prune terminal-free dangling tails only; prove every physical pad group unchanged.
No connected route between terminals may be removed. Abort/restore on mismatch.
"""
from common import *
original={t.m_Uuid.AsString() for t in b.GetTracks()};fan=json.loads((OUT/'fanouts.json').read_text())
def groups():
 b.BuildConnectivity();cn=b.GetConnectivity();out={}
 for f in b.GetFootprints():
  for a in f.Pads():
   out[a.m_Uuid.AsString()]=sorted(t.m_Uuid.AsString() for t in cn.GetConnectedItems(a) if isinstance(t,p.PAD))
 return out
baseline=groups();logs=[]
for iteration in range(20):
 d=drc('final_tails_'+str(iteration));baseline=groups();ids={e['items'][0]['uuid'] for e in d['violations'] if e['type']=='track_dangling'};ts=[t for t in b.GetTracks() if t.m_Uuid.AsString() in ids and t.m_Uuid.AsString() in original];removed=[]
 for t in ts:
  if t.GetNetname() in ['/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT']:continue
  record={'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'a':xy(t.GetStart()),'b':xy(t.GetEnd())}
  remove(t)
  if groups()!=baseline:
   b.Add(t);assert groups()==baseline;continue
  removed.append(record)
 logs.append({'iteration':iteration,'removed':removed,'all_physical_pad_connectivity_groups_unchanged':groups()==baseline});(OUT/'final_terminal_preserving_tail_cleanup.json').write_text(json.dumps(logs,indent=2));print(iteration,len(removed),flush=True)
 if not removed:break
save(True);(OUT/'final_terminal_preserving_tail_cleanup.json').write_text(json.dumps(logs,indent=2));drc('final_tails_done')
