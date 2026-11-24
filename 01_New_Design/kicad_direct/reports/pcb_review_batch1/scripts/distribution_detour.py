from local_tools import *
# Replace our long front distribution detour by a short inner-edge escape and back connection.
ids=['0b45112a-99f2-444c-bd9f-b7328ac71600','f7dfc303-53df-4d25-9ec9-e3fe992a0f1c','0b9900cb-8e86-4ed8-be3f-6205902b318f','0483ef15-a349-4101-8aca-c2ca16aad7a3','7c00b4b0-4cca-4944-96f5-f4aaf164b49f','51865ab2-e138-49b0-b06a-8950baa71310','ea9a4963-4158-44bc-a0c0-6af2e82bbe81','3a3b5d96-5e44-4aa0-a1fc-4f14af891683','ba18cee5-d580-40d9-919e-aa893268bff3','82281bfb-085f-495e-b020-914c44753331','e1c6e3c3-8713-42a9-bbda-f07b62d14238','61a50940-0755-403f-84d4-d02a52795190','cc1756c6-405b-44dd-b4e6-12ada4708662']
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in ids:remove(t)
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) or t.GetNetname()!='+3V3' or t.GetLayer()!=p.F_Cu:continue
 for get,set in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  x,y=xy(get())
  if x==119.4:set(v(119.6,y))
  elif (x,y)==(102.8,108.2):set(v(102.8,108.0))
  elif (x,y)==(106.8,108.2):set(v(106.6,108.0))
tr(xy(pad('U1',39).GetPosition()),(113.8,117.75),'+3V3',w=.15);via(113.8,117.75,'+3V3');refresh()
# This local back path reaches the same distribution net at FB1; pin-cap links remain.
a=(13.8,17.75,1);c=endpoint(pad('FB1',1));ok,n=route(a,c,b.FindNet('+3V3').GetNetCode(),True);print('distribution',ok,n,flush=True)
via(118.95,119.5,'GND');line([xy(pad('C8',2).GetPosition()),(118.15,118.6),(118.95,119.4),(118.95,119.5)],'GND',w=.15);line([xy(pad('C7',2).GetPosition()),(118.55,119.9),(118.95,119.5)],'GND',w=.15)
(OUT/'distribution_detour_replaced.json').write_text(json.dumps({'removed_new_tracks':ids,'distribution_routed':ok,'visited':n,'ground_via':[118.95,119.5]},indent=2));drc('detour_replaced')
