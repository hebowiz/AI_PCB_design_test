from local_tools import *
from collections import Counter
j=json.loads((OUT/'after/drc_cleanup2.json').read_text())
idx={str(t.m_Uuid.AsString()):t for t in b.GetTracks()}
idx.update({str(a.m_Uuid.AsString()):a for f in b.GetFootprints() for a in f.Pads()})
for e in j['unconnected_items']:
 ts=[idx.get(x['uuid']) for x in e['items']]
 if all(t is not None for t in ts):
  a,c=ts; aa,cc=endpoint(a),endpoint(c);mask,vm=masks(a.GetNetCode())
  print(a.GetNetname(),e['items'][0]['description'],e['items'][1]['description'],aa,cc,'blocked',bool(mask[r.node(*aa)]),bool(mask[r.node(*cc)]))
