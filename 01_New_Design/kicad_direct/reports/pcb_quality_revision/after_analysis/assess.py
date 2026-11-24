"""Postprocess read-only audit and create coordinate-faithful technical figures; no CAD writes."""
from pathlib import Path
import os,sys,json,math,hashlib,subprocess,shutil
from collections import Counter
sys.path.insert(0,str(Path(os.environ['TEMP'])/'a2-pcb-quality-packages'))
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent
read=lambda n:json.loads((P/(n+'.json')).read_text(encoding='utf-8'))
write=lambda n,v:(P/(n+'.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
g=read('geometry');ts=g['tracks'];ps=g['pads'];vs=g['vias'];T={t['uuid']:t for t in ts}
unique=[]
for n in sorted({t['net'] for t in ts}):
 tt=[t for t in ts if t['net']==n];length=sum(t['length'] for t in tt);u=sum(unary_union([LineString([t['a'],t['b']]) for t in tt if t['layer']==z]).length for z in [0,2]);unique.append({'net':n,'sum_mm':round(length,6),'unique_centerline_mm':round(u,6),'coincident_excess_mm':round(length-u,6)})
write('unique_lengths',unique)
rows=read('open_leaf_candidates')
for r in rows:
 if r['net']=='GND':r['assessment']='zone-return: excluded from open-stub count';continue
 pt=Point(r['end']);own=[T[u] for u in r['uuids']];layers={t['layer'] for t in own if LineString([t['a'],t['b']]).distance(pt)<.01}
 covered=any(Polygon(z['poly']).buffer(.002).covers(pt) for z in ps if z['net']==r['net'] and layers.intersection(z['layers']))
 covered=covered or (not r['via_end'] and any(pt.distance(Point(v['a']))<=v['width']/2+.002 for v in vs if v['net']==r['net']))
 covered=covered or any(LineString([t['a'],t['b']]).buffer(t['width']/2+.002).covers(pt) for t in ts if t['net']==r['net'] and t['layer'] in layers and t['uuid'] not in r['uuids'])
 r['assessment']='junction/copper-covered tip: not confirmed stub' if covered else 'exposed leaf: inspect intended use'
write('leaf_assessment',rows)

print(json.dumps(Counter(r['assessment'] for r in rows)))
