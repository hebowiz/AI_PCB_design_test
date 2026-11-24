from geom import *
def path(qs,net,w=.15):
 for a,c in zip(qs,qs[1:]):track(a,c,net,k.F_Cu,w)
# Reattach the branch at an explicit split, and retain thermal spokes.
for t in list(b.GetTracks()):
 if uid(t)=='97cdd13d-d4da-4abe-acde-3a511fe8a280':t.SetStart(v(103.45,111.1));track((103.45,111.55),(103.45,111.1),'+3V3',k.F_Cu,.25)
 if uid(t)=='bde42f4f-0c6f-4f9a-bc44-aca718144da3':remove(t)
 if uid(t)=='adfd8ec2-3a67-4e77-89e7-b5f277acd327':remove(t)
 if uid(t)=='e729e567-ad8a-4586-be53-657018b43d6b':t.SetEnd(v(114.725,130.625))
 if uid(t)=='066b8d3a-8faa-4f2e-9d9a-56a92ae2da59':t.SetEnd(v(114.725,130.625))
 if uid(t) in ['2b4b75f0-bf66-434a-aea9-8e0a469b0763','65a1d465-4216-4605-9dca-4a6bf5de8acf','9c1ff6d1-628c-4963-a857-0a0b3caeb371','9f5c5a8c-2d3f-46a0-8642-6df6ce768cc7','c4d1d9eb-0e2f-4845-803e-87929c88c009','d04a2a3c-e855-4bcd-963d-764341360f00']:remove(t)
path([(107.35,126.1),(106.85,126.6),(106.4,126.6)],'+3V3')
path([(106.4,126.6),(106.9,126.6),(107.025,126.725),(108.1375,126.725)],'+3V3',.18)
path([(106.8,126.6),(107.1,126.9),(107.1,127.2),(107.275,127.375),(108.1375,127.375)],'+3V3',.18)
# Exactly restore the U4 in-pad spoke anchor, removed as apparently redundant.
track((109.3625,136.2),(109.35,136.2),'GND',k.F_Cu,.15)
for r in json.loads((OUT/'corner_edits.json').read_text()):
 if r.get('corner')!=[109.5,109.22]:continue
 byid={uid(t):t for t in b.GetTracks()};q=r['corner']
 for old in r['before']:
  t=byid[old['uuid']]
  if old['a']==q:t.SetStart(v(*q))
  else:t.SetEnd(v(*q))
 for new in r['after'][2:]:
  if new['uuid'] in byid:remove(byid[new['uuid']])
# Keep both ESD references close, avoiding their mutual overlap.
fps['D1'].Reference().SetPosition(v(111.45,107.8));fps['D1'].Reference().SetTextSize(v(.6,.6));fps['D1'].Reference().SetTextThickness(k.FromMM(.1))
drc('last_corners')
