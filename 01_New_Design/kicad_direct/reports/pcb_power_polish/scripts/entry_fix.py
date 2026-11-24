from geom import *
# Keep the U1 approach perpendicular up to its short edge.
q=[108.25,110.88]
for r in json.loads((OUT/'corner_edits.json').read_text()):
 if r.get('corner')!=q:continue
 byid={uid(t):t for t in b.GetTracks()}
 for rr in r['before']:
  t=byid[rr['uuid']];new=(108.13,110.88) if rr['a']==[106.0,110.88] else (108.25,111.0)
  if rr['a']==q:t.SetStart(v(*new))
  else:t.SetEnd(v(*new))
 for rr in r['after'][2:]:remove(byid[rr['uuid']])
 track((108.13,110.88),(108.25,111.0),'+3V3',k.F_Cu,.15)
for t in list(b.GetTracks()):
 if uid(t)=='b86d3be0-1857-46e8-a359-01ee3837a2b2':t.SetEnd(v(103.69,107.54));track((103.69,107.54),(103.75,107.6),'/REF12K',k.F_Cu,.15)
# Explicit thermal branch to the left of the capacitor (not a signal turn).
track((109.5,109.22),(108.9,109.22),'GND',k.F_Cu,.2)
# ESD references sit between the protection parts and decouplers.
fps['D1'].Reference().SetPosition(v(110.8,107.8))
drc('entry_fix')
