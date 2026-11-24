from common import *
uid='a2d0a770-0561-44cc-8e16-c79addf7b142';t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==uid);assert t.GetNetname()=='/RXLED_N';remove(t);save();drc('signal_corridor')
