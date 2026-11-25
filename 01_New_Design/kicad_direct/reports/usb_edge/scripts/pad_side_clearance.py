from common import *
# Clear the parallel GND spine from the side of D1 pad 2 while keeping signal pin on USB trunk.
fps['D1'].Move(v(-.125,0))
for t in b.GetTracks():
 a,c=xy(t.GetStart()),xy(t.GetEnd())
 if t.GetNetname()=='GND' and a==(112.55,107.4) and c==(112.8,107.15):t.SetStart(v(112.425,107.4));t.SetEnd(v(112.8,107.025))
 if uid(t)=='d5eda4cd-7080-4ffd-9ab1-9ab6ab451688':t.SetStart(v(111.725,107.4))
drc('pad_side_clearance')
