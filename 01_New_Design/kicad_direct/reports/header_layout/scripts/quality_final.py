from common import *
ids=['66a1156b-c1cb-4f3e-ae59-ae45c1c5f465','889bb623-8173-4edc-a3eb-1201c3d331bc','b62235a7-8dfb-4f8a-bd7b-be261a061a8f','b9429b6b-beef-430f-9c33-da406827d700','d86629ca-8df5-4461-81cf-f3c3d69e59bc','d9750f0b-acfb-4b51-a0eb-7785eb600152']
for t in list(b.GetTracks()):
 if uid(t) in ids:remove(t)
 elif uid(t)=='93655795-57db-4481-8f74-faf95e31ce88':t.SetStart(v(100.65,129.05))
 elif uid(t)=='236b6805-6ff3-459c-9baa-18ce0b834cd4':t.SetEnd(v(107.125,130.625))
 elif uid(t)=='6f26cb02-02ea-4c59-90c6-b11d5293a102':t.SetEnd(v(114.81,145.0))
 elif uid(t)=='8e43d79b-9a36-4de0-b220-1cbeccd04616':t.SetEnd(v(114.61,145.2))
track((107.125,130.625),(106.95,130.8),'/FT_CTS_N');track((106.95,130.8),(106.9,130.8),'/FT_CTS_N')
track((114.81,145.0),(114.61,145.2),'USB5V_OUT',w=.5)
drc('quality_final')
