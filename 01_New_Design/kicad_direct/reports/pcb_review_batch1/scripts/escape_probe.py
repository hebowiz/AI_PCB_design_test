from common import *
rows=json.loads((OUT/'escape_audit.json').read_text());ids={r['uuid'] for r in rows if not r['ok']}
for t in b.GetTracks():
 if t.m_Uuid.AsString() in ids:print(t.m_Uuid.AsString(),t.GetNetname(),xy(t.GetStart()),xy(t.GetEnd()))
for a in fps['U4'].Pads():print('U4',a.GetNumber(),a.GetNetname(),xy(a.GetPosition()),xy(a.GetSize()),a.GetOrientationDegrees())
