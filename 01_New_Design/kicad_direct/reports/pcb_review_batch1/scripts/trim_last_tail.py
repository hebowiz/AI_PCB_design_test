from common import *
t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()=='72eb8f29-357f-4d81-9c70-ecff3a1ab811');assert xy(t.GetEnd())==(105.65,121.65);t.SetEnd(v(105.65,121.35));drc('electrical_complete')
