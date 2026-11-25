from common import *
sys.path.insert(0,str(Path(os.environ['TEMP'])/'a2-pcb-quality-packages'))
from shapely.geometry import LineString,Point,Polygon
from shapely.ops import nearest_points,unary_union

def poly(p,layer=None):
 if layer is None:layer=k.F_Cu if p.IsOnLayer(k.F_Cu) else k.B_Cu
 s=k.SHAPE_POLY_SET();p.TransformShapeToPolygon(s,layer,0,k.FromMM(.001),k.ERROR_OUTSIDE);rings=[]
 for i in range(s.OutlineCount()):
  r=s.COutline(i);pts=[xy(r.CPoint(j)) for j in range(r.PointCount())]
  if len(pts)>2:rings.append(Polygon(pts))
 return unary_union(rings)
def linegeom(t):return LineString([xy(t.GetStart()),xy(t.GetEnd())])
def points(g):
 if g.is_empty:return []
 if g.geom_type=='Point':return [g.coords[0]]
 if g.geom_type=='LineString':return [g.coords[0],g.coords[-1]]
 return [q for c in g.geoms for q in points(c)]
