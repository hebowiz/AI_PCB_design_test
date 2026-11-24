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
# Plan candidates, not deletion list. Every object remains in the source PCB.
protected={'/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT','GND'}
reasons={}
def add(net,reason):reasons.setdefault(net,set()).add(reason)
for r in read('detours'):
 if r['net']!='GND':add(r['net'],'detour')
for name,reason in [('turns_ge90','turn'),('cycles','cycle candidate'),('pad_near','pad proximity'),('pad_corridors','inter-pad')]:
 for r in read(name):add(r['net'],reason)
for r in rows:
 if r['assessment'].startswith('exposed'):add(r['net'],'leaf candidate')
for r in read('usb5v_widths'):add(r['net'],'power width')
plan=[]
for n in sorted(reasons):
 nt=[t for t in ts if t['net']==n];nv=[v for v in vs if v['net']==n]
 plan.append({'net':n,'reasons':sorted(reasons[n]),'scope':'protected geometry: inspect and preserve priority conditions; only explicitly justified local edits' if n in protected else 'net topology review and necessary reroute','segments':len(nt),'vias':len(nv),'length_mm':round(sum(t['length'] for t in nt),5),'uuids':[t['uuid'] for t in nt],'via_uuids':[v['uuid'] for v in nv]})
for r in plan:
 r['tier']='P: protected' if r['net'] in protected else 'A: topology / power trunk' if any(k in r['reasons'] for k in ['detour','cycle candidate','power width']) else 'B: local bends / pad approach / leaf'
write('proposed_scope',plan)
core=[r for r in plan if r['net'] not in protected]
summary={'leaf_classes':dict(Counter(r['assessment'] for r in rows)),'turn_angles':dict(Counter(str(r['turn_deg']) for r in read('turns_ge90'))),'detour_non_GND_pairs':sum(r['net']!='GND' for r in read('detours')),'detour_non_GND_nets':sorted({r['net'] for r in read('detours') if r['net']!='GND'}),'core_nets':len(core),'core_segments':sum(r['segments'] for r in core),'core_vias':sum(r['vias'] for r in core),'core_mm':round(sum(r['length_mm'] for r in core),5),'protected_nets':sorted(protected),'scope_is_not_removal_authorization':True,'near_gap_range_mm':[min(r['gap_mm'] for r in read('pad_near')),max(r['gap_mm'] for r in read('pad_near'))]}
summary['tiers']={k:{'nets':len([r for r in plan if r['tier']==k]),'segments':sum(r['segments'] for r in plan if r['tier']==k),'vias':sum(r['vias'] for r in plan if r['tier']==k)} for k in sorted({r['tier'] for r in plan})}
write('assessment_summary',summary)
# Native images were exported at exactly the reviewed commit; verify blob identity before copying.
root=Path('C:/Users/hebow/.codex/worktrees/a2-pcb-review/99_AI_PCB_design_test');rel='01_New_Design/kicad_direct/reports/pcb_review_batch1/after/'
provenance=[]
for name in ['front.png','back.png']:
 src=root/(rel+name);blob=subprocess.check_output(['git','hash-object',str(src)],cwd=root,text=True).strip();expected=subprocess.check_output(['git','rev-parse','5596d3b:'+rel+name],cwd=root,text=True).strip();assert blob==expected
 shutil.copyfile(src,P/('native_'+name));provenance.append({'file':'native_'+name,'source':rel+name,'git_blob':blob,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
write('image_provenance',provenance)
fontpath='C:/Windows/Fonts/arial.ttf'
F=lambda n:ImageFont.truetype(fontpath,n)
figs=[]
def fig(name,bounds,nets,marked=(),labels=(),layers=(0,2)):
 x0,y0,x1,y1=bounds;scale=min(170,1100/(x1-x0),1400/(y1-y0));W=round((x1-x0)*scale)+100;H=round((y1-y0)*scale)+130
 im=Image.new('RGB',(W,H),'#101820');d=ImageDraw.Draw(im)
 def pt(q):return (round(50+(q[0]-x0)*scale),round(85+(q[1]-y0)*scale))
 def inside(q):return x0<=q[0]<=x1 and y0<=q[1]<=y1
 def line(t,color):
  a,b=pt(t['a']),pt(t['b']);w=max(1,round(t['width']*scale));d.line([a,b],fill=color,width=w);rad=w/2
  for x,y in [a,b]:d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=color)
 d.text((15,8),name,fill='white',font=F(22));d.text((15,37),'5596d3b | F.Cu red / B.Cu blue | zones hidden | top view',fill='#dedede',font=F(15))
 for x in range(math.ceil(x0),math.floor(x1)+1):d.line([pt((x,y0)),pt((x,y1))],fill='#22313c');d.text((pt((x,y0))[0]-8,65),str(x),fill='#999999',font=F(12))
 for y in range(math.ceil(y0),math.floor(y1)+1):d.line([pt((x0,y)),pt((x1,y))],fill='#22313c');d.text((5,pt((x0,y))[1]-7),str(y),fill='#999999',font=F(12))
 for t in ts:
  if t['layer'] in layers:line(t,'#495563')
 for z in ps:
  if not set(z['layers']).intersection(layers):continue
  d.polygon([pt(q) for q in z['poly']],fill='#525657')
 for t in ts:
  if t['net'] in nets and t['layer'] in layers:line(t,'#ff6655' if t['layer']==0 else '#59b9ff')
 for z in ps:
  if z['net'] in nets and set(z['layers']).intersection(layers):
   d.polygon([pt(q) for q in z['poly']],fill='#bf9942',outline='#ffe9a0')
   if inside(z['at']):d.text(pt(z['at']),z['pin'],fill='white',font=F(13),anchor='mm')
 for v in vs:
  if not inside(v['a']):continue
  x,y=pt(v['a']);r=v['width']/2*scale;d.ellipse((x-r,y-r,x+r,y+r),outline='#f6df7b' if v['net'] in nets else '#65717b',width=2)
  r=v['hole']/2*scale;d.ellipse((x-r,y-r,x+r,y+r),fill='#101820')
 for q in marked:
  x,y=pt(q);d.ellipse((x-11,y-11,x+11,y+11),outline='#ffff00',width=3)
 for q,txt in labels:
  x,y=pt(q);d.text((x,y),txt,fill='#ffff00',font=F(17))
 # Clip geometry to plot rectangle; keep headings readable even when off-screen lines cross them.
 d.rectangle((0,0,W,64),fill='#101820');d.rectangle((0,64,45,H-35),fill='#101820');d.rectangle((W-45,64,W,H-35),fill='#101820')
 d.text((15,8),name,fill='white',font=F(22));d.text((15,37),'5596d3b | F.Cu red / B.Cu blue | zones hidden | top view',fill='#dedede',font=F(15))
 d.rectangle((0,H-35,W,H),fill='#101820');d.text((15,H-29),'Highlight: '+', '.join(sorted(nets)),fill='white',font=F(15))
 im.save(P/(name+'.png'));figs.append({'file':name+'.png','bounds_mm':bounds,'nets':sorted(nets),'layers':layers,'zones':'not shown'})
fig('01_eeprom_detour',(100,112,120,128.5),{'/EE_CLK','/EE_DATA'})
fig('02_turns',(105,114,114,124),{'+3V3'},marked=[r['at'] for r in read('turns_ge90') if r['net']=='+3V3' and 105<r['at'][0]<114 and 114<r['at'][1]<124])
fig('03_control_stub',(115.5,124.4,120,129),{'/PWREN_N'},marked=[(117,127.35)],labels=[((115.7,128.2),'Open extension at x117.0, y127.35')])
fig('04_power_loops',(111,131.8,118.5,137.2),{'VIO','/FB_2V5'})
fig('05_interpad',(111.8,126.6,115.3,128.9),{'/PWREN_N'},marked=[(113.86,127.7)],labels=[((112,128.4),'Pad gap = 0.05 mm each')],layers=(0,))
fig('06_ldo_pad_near',(107.5,133.5,110.8,136.2),{'USB5V'},marked=[(108.95,134.85)],labels=[((107.7,133.7),'U4.1 gap = 0.025 mm')],layers=(0,))
fig('07_usb5v_routes',(100,102,122,150),{'USB5V','/USB5V_SW','USB5V_OUT'})
fig('08_output_stub',(103.8,131.5,106.4,136.5),{'USB5V_OUT'},marked=[(104.9,135)],labels=[((103.9,136),'B.Cu leaf under front TP2')],layers=(2,))
write('figures',figs)
print(json.dumps(summary,indent=2));print('figures',len(figs))
