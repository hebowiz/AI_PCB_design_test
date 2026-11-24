from common import *
t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()=='72eb8f29-357f-4d81-9c70-ecff3a1ab811');b.BuildConnectivity();cn=b.GetConnectivity();print('target',xy(t.GetStart()),xy(t.GetEnd()))
for s in cn.GetConnectedTracks(t):print(s.m_Uuid.AsString(),xy(s.GetStart()),xy(s.GetEnd()))
