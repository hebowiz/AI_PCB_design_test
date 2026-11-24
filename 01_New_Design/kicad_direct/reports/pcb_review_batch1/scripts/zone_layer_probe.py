from common import *
print('enum',p.F_Cu,p.B_Cu)
for z in b.Zones():
 print('zone',z.GetLayer(),z.GetLayerName(),list(z.GetLayerSet().Seq()),z.GetIsRuleArea(),z.GetZoneName())
