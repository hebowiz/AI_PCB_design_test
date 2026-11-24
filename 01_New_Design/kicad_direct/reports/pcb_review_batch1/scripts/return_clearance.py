from common import *
# Shift the new +3V3 distribution branch around C12, freeing C3's ground return.
ids=['06e47df0-bb7c-40a7-b364-6b4b93d2bb72','9d80806b-3bb5-4db7-81bb-b643cefcabdc','ac15d1d7-a6ad-41a4-8cdb-b20078b176e1']
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in ids:remove(t)
line([(104.5,110.75),(102.8,110.75),(102.8,108.2),(106.8,108.2),(107.1,108.5)],'+3V3',w=.15)
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) or t.GetNetname()!='VPLL':continue
 for get,set in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  pt=xy(get())
  if pt==(104.5,109.55):set(v(104.3,109.35))
  elif pt==(108.9,109.55):set(v(108.7,109.35))
pad('C10',2).SetThermalSpokeAngleDegrees(0)
for z in b.Zones():
 if not z.GetIsRuleArea():print(z.GetZoneName(),'island mode',z.GetIslandRemovalMode());z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
save();drc('returns_final')
