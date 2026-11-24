import sys
sys.path.insert(0,'01_New_Design/kicad_direct/reports/pcb_power_polish/scripts')
from common import *
for t in list(b.GetTracks()):
 if uid(t) in ['ec2c8088-f1a7-43e3-a528-295ded0cb2ae','582b567c-1b3d-4cd7-8834-ec85773b0ede']:remove(t)
qs=[(107.6,126.1),(106.85,126.1),(106.4,126.55),(106.4,126.6)]
for a,c in zip(qs,qs[1:]):track(a,c,'+3V3',k.F_Cu,.15)
drc('c16_order')
