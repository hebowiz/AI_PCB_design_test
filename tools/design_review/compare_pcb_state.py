"""Read-only PCB invariant and routing-regression comparison (KiCad Python)."""
import argparse,hashlib,json,math,sys,collections
from pathlib import Path
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--before',type=Path,required=True);ap.add_argument('--after',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--packages',type=Path,required=True);a=ap.parse_args();sys.path.insert(0,str(a.packages))
import pcbnew as k
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
xy=lambda q:[round(k.ToMM(q.x),6),round(k.ToMM(q.y),6)]
uid=lambda q:q.m_Uuid.AsString()
def poly(s):
 def ring(r):return [xy(r.CPoint(i)) for i in range(r.PointCount())]
 return unary_union([Polygon(ring(s.COutline(i)),[ring(s.CHole(i,j)) for j in range(s.HoleCount(i))]) for i in range(s.OutlineCount())])
def state(path):
 b=k.LoadBoard(str(path));keep=list(b.GetTracks());fps={};pads=[];tracks={};escape=[];angles=[]
 for f in b.GetFootprints():
  pp=[]
  for p in f.Pads():
   pp.append({'uuid':uid(p),'number':p.GetNumber(),'net':p.GetNetname(),'position':xy(p.GetPosition()),'size':xy(p.GetSize()),'drill':xy(p.GetDrillSize()),'angle':p.GetOrientationDegrees(),'shape':p.GetShape(),'attribute':p.GetAttribute(),'layers':p.GetLayerSet().FmtBin()})
   for layer in [k.F_Cu,k.B_Cu]:
    if p.IsOnLayer(layer):
     s=k.SHAPE_POLY_SET();p.TransformShapeToPolygon(s,layer,0,k.FromMM(.001),k.ERROR_OUTSIDE);pads.append({'pin':f.GetReference()+'.'+p.GetNumber(),'net':p.GetNetname(),'layer':layer,'geom':poly(s)})
  fps[f.GetReference()]={'uuid':uid(f),'value':f.GetValue(),'footprint':f.GetFPID().GetLibItemName(),'position':xy(f.GetPosition()),'angle':f.GetOrientationDegrees(),'layer':f.GetLayer(),'attributes':f.GetAttributes(),'pads':sorted(pp,key=lambda r:r['uuid'])}
 for t in keep:
  isvia=isinstance(t,k.PCB_VIA);r={'uuid':uid(t),'net':t.GetNetname(),'a':xy(t.GetStart()),'b':xy(t.GetEnd()),'layer':t.GetLayerName(),'width_mm':k.ToMM(t.GetWidth(k.F_Cu) if isvia else t.GetWidth()),'via':isvia}
  if isvia:r['drill_mm']=k.ToMM(t.GetDrillValue())
  else:
   r['length_mm']=k.ToMM(t.GetLength());dx,dy=abs(r['a'][0]-r['b'][0]),abs(r['a'][1]-r['b'][1])
   if min(dx,dy)>.0001 and abs(dx-dy)>.0001:angles.append(r)
  tracks[uid(t)]=r
 for f in b.GetFootprints():
  if f.GetReference() not in ['U1','U2','U4','U5']:continue
  for p in f.Pads():
   if not p.GetNetCode() or p.GetNetname().startswith('unconnected-'):continue
   cx,cy=xy(p.GetPosition());sx,sy=xy(p.GetSize());ang=math.radians(p.GetOrientationDegrees());co,si=math.cos(ang),math.sin(ang);long=0 if sx>=sy else 1;half=[sx/2,sy/2]
   def local(pt):dx,dy=pt[0]-cx,pt[1]-cy;return [dx*co-dy*si,dx*si+dy*co]
   for r in tracks.values():
    if r['via'] or r['net']!=p.GetNetname() or r['layer']!='F.Cu':continue
    x,y=local(r['a']),local(r['b'])
    for axis in [0,1]:
     delta=y[axis]-x[axis]
     if abs(delta)<1e-8:continue
     for sign in [-1,1]:
      u=(sign*half[axis]-x[axis])/delta
      if not -.00001<=u<=1.00001:continue
      off=x[1-axis]+u*(y[1-axis]-x[1-axis])
      if abs(off)<=half[1-axis]+.00001:escape.append({'pin':f.GetReference()+'.'+p.GetNumber(),'uuid':r['uuid'],'short_edge':axis==long,'offset_mm':round(off,6),'ok':axis==long and abs(off)<.001})
 ground={}
 for layer in [k.F_Cu,k.B_Cu]:
  objs=[p['geom'] for p in pads if p['net']=='GND' and p['layer']==layer]
  for z in b.Zones():
   if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(layer):objs.append(poly(z.GetFilledPolysList(layer)))
  for t in keep:
   if t.GetNetname()=='GND':
    if isinstance(t,k.PCB_VIA):objs.append(Point(xy(t.GetPosition())).buffer(k.ToMM(t.GetWidth(layer))/2))
    elif t.GetLayer()==layer:objs.append(LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(k.ToMM(t.GetWidth())/2))
  ground[b.GetLayerName(layer)]=unary_union(objs)
 edge=sorted([{'uuid':uid(e),'shape':e.GetShape(),'a':xy(e.GetStart()),'b':xy(e.GetEnd())} for e in b.GetDrawings() if e.GetLayer()==k.Edge_Cuts],key=lambda r:r['uuid'])
 rule_areas=[{'uuid':uid(z),'name':z.GetZoneName(),'layers':z.GetLayerSet().FmtBin(),'outline':poly(z.Outline()).wkt} for z in b.Zones() if z.GetIsRuleArea()]
 return {'board':b,'keep':keep,'footprints':fps,'tracks':tracks,'ground':ground,'edge':edge,'rule_areas':rule_areas,'thickness_mm':k.ToMM(b.GetDesignSettings().GetBoardThickness()),'layer_count':b.GetCopperLayerCount(),'escape':escape,'non45':angles}
bs,as_=state(a.before),state(a.after);bt,at=bs['tracks'],as_['tracks'];removed=[bt[u] for u in bt.keys()-at.keys()];added=[at[u] for u in at.keys()-bt.keys()];modified=[{'before':bt[u],'after':at[u]} for u in bt.keys()&at.keys() if bt[u]!=at[u]]
protected=['/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT'];refs=[]
for net in protected:
 for layer,opposite in [('F.Cu','B.Cu'),('B.Cu','F.Cu')]:
  region=unary_union([LineString([t['a'],t['b']]).buffer(t['width_mm']/2) for t in at.values() if not t['via'] and t['net']==net and t['layer']==layer])
  loss=region.intersection(bs['ground'][opposite]).difference(as_['ground'][opposite].buffer(.002))
  refs.append({'net':net,'signal_layer':layer,'new_reference_loss_over_2um_mm2':loss.area,'before_unreferenced_mm2':region.difference(bs['ground'][opposite]).area,'after_unreferenced_mm2':region.difference(as_['ground'][opposite]).area})
result={'before_sha256':hashlib.sha256(a.before.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(a.after.read_bytes()).hexdigest(),'checks':{'footprints_and_pads_unchanged':bs['footprints']==as_['footprints'],'edge_unchanged':bs['edge']==as_['edge'],'rule_areas_unchanged':bs['rule_areas']==as_['rule_areas'],'thickness_1_6mm':bs['thickness_mm']==as_['thickness_mm']==1.6,'two_layers':bs['layer_count']==as_['layer_count']==2,'protected_usb_crystal_routes_unchanged':{u:r for u,r in bt.items() if r['net'] in protected}=={u:r for u,r in at.items() if r['net'] in protected},'no_new_reference_loss':all(x['new_reference_loss_over_2um_mm2']<.001 for x in refs),'via_dimensions':all(r['drill_mm']==.3 and r['width_mm']==.6 for r in at.values() if r['via']),'no_non45_segments':not as_['non45'],'all_ic_pad_exits_short_edge_center':all(x['ok'] for x in as_['escape'])},'footprint_count':len(as_['footprints']),'pad_count':sum(len(f['pads']) for f in as_['footprints'].values()),'reference_coverage':refs,'ic_escape_before':bs['escape'],'ic_escape_after':as_['escape'],'removed':removed,'added':added,'modified':modified,'zone_note':'GND outline cutouts/fill may differ; protected rule areas must not.'}
a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result['checks'],indent=2));print('tracks/vias changed',len(removed),len(added),len(modified))
