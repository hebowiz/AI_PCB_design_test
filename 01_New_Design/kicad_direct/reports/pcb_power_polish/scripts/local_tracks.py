from geom import *
from shapely.geometry import box
region=box(102,106.5,110,111.1)
for t in b.GetTracks():
 if t.GetNetname() in ['GND','+3V3','USB5V','VIO']:
  if (Point(xy(t.GetPosition())) if isinstance(t,k.PCB_VIA) else linegeom(t)).intersects(region):print(record(t))
