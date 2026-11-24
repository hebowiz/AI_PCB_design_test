from common import *
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in ['624cfcf9-3ac7-460a-8e26-7211a02538be','9c51b535-a767-4d75-8af9-579b1667238b','556aeec7-d209-4222-9624-dda36e57a62a']:remove(t)
 elif isinstance(t,p.PCB_VIA) and t.m_Uuid.AsString()=='a3fdd950-2015-4d32-b781-aab7571484b5':t.SetPosition(v(108.15,137.1))
 elif not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/RTS_N' and t.GetLayer()==p.B_Cu and xy(t.GetStart())==(107.85,137.1) and xy(t.GetEnd())==(108.15,137.1):remove(t)
tr((107.9,137.1),(108.15,137.1),'/RTS_N',w=.15)
line([(108.95,136.75),(110.25,136.75),(110.25,137.15),(109.3625,137.15)],'/PWR_EN',w=.15)
drc('escape_final')
