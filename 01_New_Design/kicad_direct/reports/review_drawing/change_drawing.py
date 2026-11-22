"""Local schematic review edits, guarded against replay on edited source."""
from pathlib import Path
import os,sys,copy,uuid,subprocess,json,hashlib,datetime,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent; R=H.parents[1]; ROOT=R.parents[1]
sys.path.insert(0,str(R/'scripts'));from sexpr import *
BASE='886ad5428d4be98768ccc8bb942aa2f54f23d942';REL='01_New_Design/kicad_direct/a2_usb_uart.kicad_sch';source=ROOT/REL
cli=Path(os.environ['LOCALAPPDATA'])/'Programs/KiCad/10.0/bin/kicad-cli.exe'
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
def uid():return Q(str(uuid.uuid4()))
def prop(o,n):return next(p for p in children(o,'property') if p[1]==n)
def ref(o):return str(prop(o,'Reference')[2])
def mm(x):return round(x*1.27,5)
def pt(x,y):return [mm(x),mm(y)]
log=json.loads((H/'commands.json').read_text()) if (H/'commands.json').exists() else []
def run(cmd,accept=(0,)):
 p=subprocess.run(list(map(str,cmd)),cwd=ROOT,capture_output=True)
 log.append(dict(at=datetime.datetime.now().astimezone().isoformat(),command=list(map(str,cmd)),exit_code=p.returncode,stdout=p.stdout.decode('utf8','replace'),stderr=p.stderr.decode('utf8','replace')))
 (H/'commands.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf8')
 if p.returncode not in accept:raise RuntimeError(log[-1])
def export(v):
 out=H/v;out.mkdir(exist_ok=True)
 (out/'a2_usb_uart.kicad_sch').write_bytes(source.read_bytes())
 for args,name in [(['export','netlist','--format','kicadxml'],'netlist.xml'),(['erc','--format','json','--exit-code-violations'],'erc.json'),(['export','pdf','--black-and-white'],'schematic.pdf')]:run([cli,'sch',*args,'-o',out/name,source],(0,5) if name=='erc.json' else (0,))
 run(['pdftoppm','-scale-to','5600','-png','-singlefile',out/'schematic.pdf',out/'schematic'])

base=git('show',BASE+':'+REL)
if '--export-after' not in sys.argv:
 assert source.read_bytes()==base,'Refuse to overwrite edited source'
 export('before');s=parse(base.decode('utf8'));objs={ref(o):o for o in children(s,'symbol')}
 def move(r,x,y):
  o=objs[r];a=one(o,'at');ox,oy=map(float,a[1:3]);nx,ny=pt(x,y);a[1:3]=[nx,ny]
  for p in children(o,'property'):
   a=one(p,'at');a[1]=round(float(a[1])+nx-ox,5);a[2]=round(float(a[2])+ny-oy,5)
 def wire(a,b):s.append(['wire',['pts',['xy',*pt(*a)],['xy',*pt(*b)]],['stroke',['width',0.1524],['type','default']],['uuid',uid()]])
 def cut(a,b):
  m=[w for w in children(s,'wire') if {tuple(map(float,p[1:])) for p in one(w,'pts')[1:]}=={tuple(pt(*a)),tuple(pt(*b))}];assert len(m)==1,(a,b);s.remove(m[0])
 def dot(x,y):s.append(['junction',['at',*pt(x,y)],['diameter',0.762],['color',0,0,0,0],['uuid',uid()]])
 def undot(points):
  for j in children(s,'junction'):
   if tuple(round(float(v)/1.27,4) for v in one(j,'at')[1:3]) in points:s.remove(j)
 def clone(src,dst,x,y):
  o=copy.deepcopy(objs[src]);prop(o,'Reference')[2]=Q(dst);one(o,'uuid')[1]=uid()
  for p in children(o,'pin'):one(p,'uuid')[1]=uid()
  for pr in children(one(o,'instances'),'project'):
   for p in children(pr,'path'):one(p,'reference')[1]=Q(dst)
  objs[dst]=o;s.append(o);move(dst,x,y);return o
 def labelpos(r,x,y):
  for name,yy in [('Reference',y-1),('Value',y+1)]:
   p=prop(objs[r],name);one(p,'at')[1:]=[*pt(x,yy),0];e=one(p,'effects');j=one(e,'justify')
   if j:j[1:]=['right']
   else:e.append(['justify','right'])
 # R-0009: source -> capacitor branch -> VCCIO pin, separate supply symbols.
 for a,b in [((108,86),(128,86)),((128,86),(138,86)),((128,86),(128,81)),((124,81),(128,81)),((128,81),(153,81)),((124,81),(124,82)),((124,88),(124,89)),((138,86),(143,86)),((143,86),(143,87)),((143,87),(153,87)),((138,92),(138,93))]:cut(a,b)
 undot([(124,81),(128,81),(128,86),(138,86)])
 move('C3',134,85);move('#PWR0151',134,89);labelpos('C3',131,85);move('#PWR0109',130,79)
 move('C4',142,90);move('#PWR0152',142,94);labelpos('C4',139,90)
 clone('#PWR0109','#PWR0177',138,87)
 for a,b in [((130,79),(130,81)),((130,81),(134,81)),((134,81),(153,81)),((134,81),(134,82)),((134,88),(134,89)),((138,87),(142,87)),((142,87),(153,87)),((142,93),(142,94))]:wire(a,b)
 dot(134,81);dot(142,87)
 # R-0010: source -> bulk C1 -> local C23 -> U1.40.
 for a,b in [((146,101),(146,129)),((146,129),(150,129)),((150,129),(150,131)),((150,131),(162,131)),((150,137),(150,138)),((162,137),(162,138))]:cut(a,b)
 undot([(150,131)])
 move('#PWR0174',122,135);move('C1',130,138);move('#PWR0149',130,142);labelpos('C1',127,138)
 move('C23',142,138);move('#PWR0176',142,142)
 for a,b in [((122,135),(130,135)),((130,135),(142,135)),((142,135),(146,135)),((146,135),(146,101)),((130,141),(130,142)),((142,141),(142,142))]:wire(a,b)
 dot(130,135);dot(142,135)
 # R-0011: flag on a straight horizontal wire, no overlap with its own stem.
 cut((130,100),(141,100));wire((130,100),(136,100));wire((136,100),(141,100));move('#FLG07',136,100);undot([(141,100)]);dot(136,100)
 # R-0012: reorder routing tracks without changing the terminal endpoints.
 oldpaths=[[(58,48),(58,29),(187,29),(187,67),(177,67)],[(74,46),(74,27),(189,27),(189,65),(177,65)],[(93,32),(137,32),(137,63),(153,63)],[(117,34),(139,34),(139,65),(153,65)]]
 newpaths=[[(58,48),(58,27),(189,27),(189,67),(177,67)],[(74,46),(74,29),(187,29),(187,65),(177,65)],[(93,32),(139,32),(139,63),(153,63)],[(117,34),(137,34),(137,65),(153,65)]]
 for path in oldpaths:
  for a,b in zip(path,path[1:]):cut(a,b)
 for path in newpaths:
  for a,b in zip(path,path[1:]):wire(a,b)
 for l in children(s,'label'):
  if str(l[1])=='USB_D+':one(l,'at')[1:3]=pt(151,27)
  if str(l[1])=='USB_D-':one(l,'at')[1:3]=pt(151,29)
 # R-0013: compress whitespace between groups, preserve each symbol and pin spacing.
 def grid(a):return [round(float(v)/1.27,5) for v in a]
 def block(x,y):return x<235 and y>170
 def mapped(x,y):
  nx=x
  if y>=292:
   if x>=160:nx=x-55
   ny=y-46
  elif y>=277:ny=y-47
  elif y>=269:ny=y-45
  elif y>=256:ny=y-44
  elif y==249:ny=210
  elif y>=230:
   ny=y-38
   if x>=174:nx=x-35
  elif y==202:ny=185
  else:ny=y
  return nx,ny
 for o in children(s,'symbol'):
  x,y=grid(one(o,'at')[1:3])
  if block(x,y):move(ref(o),*mapped(x,y))
 for kind in ['wire']:
  for o in children(s,kind):
   pts=one(o,'pts')[1:]
   if all(block(*grid(p[1:3])) for p in pts):
    for p in pts:p[1:3]=pt(*mapped(*grid(p[1:3])))
 for kind in ['junction','label','no_connect']:
  for o in children(s,kind):
   a=one(o,'at');x,y=grid(a[1:3])
   if block(x,y):a[1:3]=pt(*mapped(x,y))
 # Compact related explanations; retain the existing drawing notes elsewhere.
 newtext={
 'USB5V -> U1.40 VREGIN; C1 4.7uF + C23 100nF.':('USB5V -> U1.40 (C1/C23); U1.39 -> +3V3 (C2/C5).',24,265),
 'U1.39 VCCD -> C2 / +3V3 -> bridge / EEPROM / control.':('+3V3 supplies bridge / EEPROM / control.',24,270),
 'U1.39 output is declared by a flag in block 01.':('U1 output flag and capacitors: block 01. PCB update pending.',24,275),
 'U4: variable VIO -> U2 VCCB':('U4: variable VIO -> U2 VCCB',160,237),
 'SW3 switches the header supply only.':('SW3 switches the header supply only.',160,241),
 'UART VIO remains connected.':('UART VIO remains connected.',160,245),
 'SW1: open=1.8V / R9=2.5V / R10=3.3V':('SW1: open=1.8V / R9=2.5V / R10=3.3V',78,239),
 'USB5V -> SW2 -> USB5V_OUT. Manual output, independent of USB configuration / suspend.':('USB5V -> SW2 -> USB5V_OUT. Manual output, independent of USB configuration / suspend.',48,256),
 'C1 + C23 -> U1.40 (VREGIN)':('C1 + C23 -> U1.40 (VREGIN)',122,147),
 'R-0007/8 revised; PCB/BOM not updated.':('R-0009..13 drawing revised; PCB/BOM not updated.',350,246),
 'R-0007/8: human review pending. Not for fabrication.':('R-0009..13: human review pending. Not for fabrication.',350,274)}
 for t in children(s,'text'):
  text=str(t[1])
  if text=='C1/C2 connections are drawn at U1. PCB update pending.':s.remove(t)
  elif text in newtext:
   text,x,y=newtext[text];t[1]=Q(text);one(t,'at')[1:3]=pt(x,y)
 # Visual pass 2: clear annotations and bring SW3 next to the VIO output.
 for l in children(s,'label'):
  if str(l[1])=='FB_3V3':one(l,'at')[1:3]=pt(106,227)
 for z in children(s,'text'):
  if str(z[1])=='C1 + C23 -> U1.40 (VREGIN)':one(z,'at')[1:3]=pt(122,145)
 for a,b in [((95,192),(139,192)),((139,192),(155,192)),((155,192),(155,194)),((155,194),(163,194)),((187,193),(193,193)),((193,193),(197,193))]:cut(a,b)
 undot([(139,192),(193,193)])
 move('SW3',134,193);move('#PWR0120',104,192);move('#PWR0121',156,193);move('#FLG06',152,193)
 for n in children(s,'no_connect'):
  if grid(one(n,'at')[1:3])==[163,192]:one(n,'at')[1:3]=pt(122,192)
 for a,b in [((95,192),(104,192)),((104,192),(114,192)),((114,192),(114,194)),((114,194),(122,194)),((146,193),(152,193)),((152,193),(156,193))]:wire(a,b)
 dot(104,192);dot(152,193)
 # Visual pass 3: keep the FB_3V3 label left of the adjacent FB_2V5 vertical wire.
 for l in children(s,'label'):
  if str(l[1])=='FB_3V3':
   e=one(l,'effects');j=one(e,'justify')
   if j:j[1:]=['right','bottom']
   else:e.append(['justify','right','bottom'])
 one(one(s,'title_block'),'rev')[1]=Q('A2-DRAWING REVIEW')
 source.write_text(dump(s)+'\n',encoding='utf8')
export('after')
from PIL import Image,ImageDraw
boxes={'power_pins':(100,72,178,151),'flag':(104,94,154,104),'pairs':(38,23,195,70),'power_block':(15,166,237,319)}
for v in ['before','after']:
 im=Image.open(H/v/'schematic.png').convert('RGB');f=im.width/(594/1.27)
 for name,b in boxes.items():im.crop(tuple(round(x*f) for x in b)).save(H/v/(name+'.png'))
 im.resize((1680,1188)).save(H/v/'overview.png')
for name in boxes:
 ims=[Image.open(H/v/(name+'.png')) for v in ['before','after']];im=Image.new('RGB',(sum(i.width for i in ims),max(i.height for i in ims)+30),'white');d=ImageDraw.Draw(im);x=0
 for title,p in zip(['Before 886ad54','After R-0009..13'],ims):im.paste(p,(x,30));d.text((x+10,10),title,fill='black');x+=p.width
 im.save(H/('comparison_'+name+'.png'))
def pins(p):return {n.get('ref')+'.'+n.get('pin'):net.get('name') for net in ET.parse(p).findall('.//nets/net') for n in net.findall('node')}
def parts(p):return {e.get('ref'):e for e in ET.parse(p).findall('.//components/comp')}
a=pins(H/'before/netlist.xml');b=pins(H/'after/netlist.xml');ca=parts(H/'before/netlist.xml');cb=parts(H/'after/netlist.xml')
sa=parse(base.decode('utf8'));sb=parse(source.read_text());oa={ref(o):o for o in children(sa,'symbol')};ob={ref(o):o for o in children(sb,'symbol')}
props=lambda o:{str(p[1]):str(p[2]) for p in children(o,'property')}
checks={'all_terminal_nets_identical':a==b,'all_real_parts_identical':set(ca)==set(cb),'all_real_attributes_identical':all(props(oa[r])==props(ob[r]) for r in ca),'all_original_symbol_UUIDs_preserved':all(one(oa[r],'uuid')==one(ob[r],'uuid') for r in oa),'symbol_definitions_identical':one(sa,'lib_symbols')==one(sb,'lib_symbols'),'DNP_and_BOM_flags_identical':all(all(one(oa[r],k)==one(ob[r],k) for k in ['dnp','in_bom','on_board']) for r in oa),'only_one_power_symbol_added':set(ob)-set(oa)=={'#PWR0177'} and not(set(oa)-set(ob))}
for v in ['before','after']:
 er=json.loads((H/v/'erc.json').read_text());checks[v+'_ERC_zero']=not [i for sh in er['sheets'] for i in sh['violations']]
checks['ERC_config_unchanged']=json.loads((H/'before/erc.json').read_text())['ignored_checks']==json.loads((H/'after/erc.json').read_text())['ignored_checks']
basefiles=set(git('ls-tree','-r','--name-only',BASE).decode().splitlines());allchanged=git('diff','--name-only',BASE).decode().splitlines();changed=[f for f in allchanged if f in basefiles];checks['protected_files_unchanged']=changed==[REL] and all(f in basefiles or f.startswith('01_New_Design/kicad_direct/reports/review_drawing/') for f in allchanged)
report={'timestamp':datetime.datetime.now().astimezone().isoformat(),'base':BASE,'checks':checks,'all_pass':all(checks.values()),'components':[len(ca),len(cb)],'terminals':[len(a),len(b)],'nets':[len(set(a.values())),len(set(b.values()))],'terminal_delta':{k:[a.get(k),b.get(k)] for k in set(a)|set(b) if a.get(k)!=b.get(k)},'modified_existing_files':changed,'source_sha256':sha(source.read_bytes())}
(H/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(H/'export_manifest.json').write_text(json.dumps({str(p.relative_to(H)):sha(p.read_bytes()) for v in ['before','after'] for p in (H/v).iterdir() if p.is_file()},indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2));assert report['all_pass']
