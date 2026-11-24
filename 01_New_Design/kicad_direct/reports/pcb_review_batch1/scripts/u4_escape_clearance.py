from common import *
t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()=='a3fdd950-2015-4d32-b781-aab7571484b5');assert xy(t.GetPosition())==(108.15,137.1);t.SetPosition(v(107.85,137.1))
s=next(t for t in b.GetTracks() if t.m_Uuid.AsString()=='5eb0fd4f-dbfa-4e78-900f-6a441dfd1fc2');remove(s);tr((107.85,137.1),(108.15,137.1),'/RTS_N',p.B_Cu,.15);drc('escape_complete')
