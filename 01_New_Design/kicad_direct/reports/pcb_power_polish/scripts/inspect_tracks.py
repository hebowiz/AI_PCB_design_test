from geom import *
for net in ['VPLL','VPHY','+3V3','USB5V','VIO']:
 print('\nNET',net)
 for t in b.GetTracks():
  if t.GetNetname()==net:print(record(t))
