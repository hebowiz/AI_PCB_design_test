from common import *
fixes={
'a5581c2d-7a2d-4b8f-8eb0-ca9d09ec5d53':[(108.1375,129.325),(109.175,129.325),(109.2,129.3),(109.4,129.3)],
'479aca0f-12d9-424c-8bee-6643fdc434f4':[(113.8625,130.625),(114.675,130.625),(114.7,130.6)],
'9200d12c-0557-4320-8af1-30fe7fb335c0':[(108.95,134.85),(108.55,134.85),(108.15,135.25),(107.98,135.25)],
'30aec6d3-0c14-42db-a424-43c823010866':[(108.95,136.75),(108.4,136.75),(108.4,137.15),(109.3625,137.15)],
'bdd247c7-c52f-4dc4-aee4-5c15cb0df627':[(111.6375,137.15),(112.5,137.15),(112.6,137.25),(113.3,137.25)],
'be188576-38b0-4b5f-83b9-1fc05560a83b':[(111.6375,135.25),(112.55,135.25),(113.4,134.4),(113.4,134.275)]}
log=[]
for uid,pts in fixes.items():
 t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==uid);net=t.GetNetname();width=p.ToMM(t.GetWidth());remove(t);line(pts,net,w=width);log.append({'replaced':uid,'net':net,'points':pts})
for q in json.loads((OUT/'non45_segments.json').read_text()):
 t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==q['uuid']);a,c=t.GetStart(),t.GetEnd();assert any(pad.HitTest(a) and pad.HitTest(c) and pad.GetNetCode()==t.GetNetCode() for f in b.GetFootprints() for pad in f.Pads());remove(t)
(OUT/'short_edge_corrections.json').write_text(json.dumps(log,indent=2));drc('short_edges')
