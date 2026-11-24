from common import *
t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()=='ae00d988-e5cc-4d5a-ab46-6ef36ffadae6');remove(t);drc('pre_simplify');ts=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)];print('segments',len(ts),'short',sum(p.ToMM(t.GetLength())<.3 for t in ts))
