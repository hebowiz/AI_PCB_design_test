from common import *
for z in b.Zones():
 if z.GetIsRuleArea():continue
 shape=z.GetFilledPolysList(z.GetLayer());print('ZONE',z.GetLayerName(),'polygons',shape.OutlineCount())
 for i in range(shape.OutlineCount()):
  c=shape.COutline(i);bb=c.BBox();print(i,abs(c.Area())/1e12,xy(bb.GetOrigin()),xy(bb.GetEnd()))
