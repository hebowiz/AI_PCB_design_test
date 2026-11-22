"""R-0016: guarded local electrical change; never regenerate approved schematic."""
from pathlib import Path
import os,sys,copy,uuid,subprocess,json,hashlib,datetime,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent; R=H.parents[1]; ROOT=R.parents[1]
sys.path.insert(0,str(R/'scripts'));from sexpr import *
BASE='fa741e9e1f7853efc5d27d3cb2c969a86abb31a1';REL='01_New_Design/kicad_direct/a2_usb_uart.kicad_sch';source=ROOT/REL
cli=Path(os.environ['LOCALAPPDATA'])/'Programs/KiCad/10.0/bin/kicad-cli.exe'
share=cli.parent.parent/'share/kicad'
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
 assert source.read_bytes()==base,'Refuse replay on edited source'
 export('before');s=parse(base.decode('utf8'));objs={ref(o):o for o in children(s,'symbol')}
 def move(r,x,y):
  o=objs[r];a=one(o,'at');dx,dy=mm(x)-float(a[1]),mm(y)-float(a[2]);a[1:3]=pt(x,y)
  for p in children(o,'property'):
   a=one(p,'at');a[1]=round(float(a[1])+dx,5);a[2]=round(float(a[2])+dy,5)
 def cut(a,b):
  found=[w for w in children(s,'wire') if {tuple(map(float,p[1:3])) for p in one(w,'pts')[1:]}=={tuple(pt(*a)),tuple(pt(*b))}]
  assert len(found)==1,(a,b);s.remove(found[0])
 def wire(a,b):s.append(['wire',['pts',['xy',*pt(*a)],['xy',*pt(*b)]],['stroke',['width',0.1524],['type','default']],['uuid',uid()]])
 def junction(x,y):s.append(['junction',['at',*pt(x,y)],['diameter',0.762],['color',0,0,0,0],['uuid',uid()]])
 def label(t,x,y,a=0):s.append(['label',Q(t),['at',*pt(x,y),a],['effects',['font',['size',1.05,1.05]],['justify','left','bottom']],['uuid',uid()]])
 def note(t,x,y):s.append(['text',Q(t),['at',*pt(x,y),0],['effects',['font',['size',1.05,1.05]],['justify','left','bottom']],['uuid',uid()]])
 def setprop(o,n,value,x,y,angle=0,justify='left',hide=False):
  p=next((p for p in children(o,'property') if p[1]==n),None)
  if p is None:p=['property',Q(n),Q(value),['at',*pt(x,y),angle],['effects',['font',['size',1.27,1.27]]]];o.append(p)
  p[2]=Q(value);one(p,'at')[1:]=[*pt(x,y),angle]
  e=one(p,'effects');e[:]=['effects',['font',['size',1.27,1.27]]]
  if justify:e.append(['justify',justify])
  if hide:e.append(['hide','yes'])
 def newinstance(o,r,x,y,angle):
  one(o,'at')[1:]=[*pt(x,y),angle];one(o,'uuid')[1]=uid()
  for p in children(o,'pin'):one(p,'uuid')[1]=uid()
  one(one(one(o,'instances'),'project'),'path')[2][1]=Q(r)
  s.append(o);return o
 for a,b in [((140,247),(146,247)),((146,247),(154,247))]:cut(a,b)
 for j in children(s,'junction'):
  if list(map(float,one(j,'at')[1:3]))==pt(146,247):s.remove(j)
 move('#FLG05',188,247);move('#PWR0123',198,247)
 r=newinstance(copy.deepcopy(objs['R1']),'R17',164,247,90)
 for n,v in {'Reference':'R17','Value':'0R / 0603','MPN':'CR0603-J/-000EPF','Footprint':'A2:R_0603_Bourns_CRPF','Datasheet':'https://www.bourns.com/docs/product-datasheets/cr-pf.pdf','Note':'Normally fitted jumper; no overcurrent protection. PPTC replacement requires land-pattern and electrical requalification.'}.items():setprop(r,n,v,164,251 if n=='Reference' else 253,90 if n in ['Reference','Value'] else 0,None,n not in ['Reference','Value'])
 # Add the standard one-pin test point symbol; existing library definitions untouched.
 lib=next(o for o in children(parse((share/'symbols/Connector.kicad_sym').read_text()),'symbol') if o[1]=='TestPoint');lib=copy.deepcopy(lib);lib[1]=Q('Connector:TestPoint');one(s,'lib_symbols').append(lib)
 for name,x in [('TP1',148),('TP2',180)]:
  o=copy.deepcopy(r);one(o,'lib_id')[1]=Q('Connector:TestPoint');one(o,'in_bom')[1]='no'
  for p in children(o,'pin'):o.remove(p)
  o.append(['pin',Q('1'),['uuid',uid()]])
  o=newinstance(o,name,x,251,180)
  for n,v in {'Reference':name,'Value':'D1.5mm','Footprint':'A2:TestPoint_Pad_D1.5mm','MPN':'PCB copper pad; no fitted component','Datasheet':'','Note':'Exposed F.Cu pad, diameter 1.5mm, no solder paste. Remove R17 and bridge TP1/TP2 with an ammeter for current measurement.'}.items():setprop(o,n,v,x+3,254 if n=='Reference' else 256,0,'right',n not in ['Reference','Value'])
 for a,b in [((140,247),(148,247)),((148,247),(161,247)),((167,247),(180,247)),((180,247),(188,247)),((188,247),(198,247)),((148,247),(148,251)),((180,247),(180,251))]:wire(a,b)
 for x in [148,180,188]:junction(x,247)
 label('USB5V_SW',148,251,180)
 for t in children(s,'text'):
  if str(t[1]).startswith('USB5V -> SW2 -> USB5V_OUT.'):t[1]=Q('USB5V -> SW2 -> R17 -> J2.4. Manual output; independent of USB configuration / suspend.');one(t,'at')[1:3]=pt(104,265)
  if str(t[1])=='USB5V -> SW2 -> USB5V_OUT (manual only)':t[1]=Q('USB5V -> SW2 -> R17 -> USB5V_OUT (manual only)')
  if 'R-0014/15' in str(t[1]):t[1]=Q(str(t[1]).replace('R-0014/15 drawing revised','R-0016 circuit revised').replace('R-0014/15: human review pending','R-0016: human review pending'))
 note('R17: normally 0R; NO overcurrent protection. Load: 10-20mA average / ~50mA peak.',104,270)
 note('Current measurement: remove R17, then connect ammeter between TP1 and TP2.',104,275)
 note('PPTC option is NOT a qualified drop-in replacement. Check lands, temperature and trip behavior.',104,280)
 source.write_text(dump(s)+'\n',encoding='utf8')
 # Only register a standard symbol library and add new footprints; never edit existing definitions.
 table=R/'sym-lib-table';t=parse(table.read_text());assert not any(one(l,'name')[1]=='Connector' for l in children(t,'lib'))
 t.append(['lib',['name',Q('Connector')],['type',Q('KiCad')],['uri',Q('${KICAD10_SYMBOL_DIR}/Connector.kicad_sym')],['options',Q('')],['descr',Q('Standard test-point symbol for R-0016')]])
 table.write_text(dump(t)+'\n',encoding='utf8')
 fp=R/'libraries/A2.pretty';tp=share/'footprints/TestPoint.pretty/TestPoint_Pad_D1.5mm.kicad_mod';assert not (fp/tp.name).exists();(fp/tp.name).write_bytes(tp.read_bytes())
 name='R_0603_Bourns_CRPF';assert not (fp/(name+'.kicad_mod')).exists()
 (fp/(name+'.kicad_mod')).write_text('''(footprint "R_0603_Bourns_CRPF" (version 20241229) (generator "pcbnew") (layer "F.Cu")
 (descr "Bourns CR0603-PF manufacturer recommended midpoint: gap 0.8, span 2.1, width 0.9 mm. NOT PPTC-qualified.")
 (attr smd)
 (fp_text reference "REF**" (at 0 -1.2) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
 (fp_text value "R_0603_Bourns_CRPF" (at 0 1.2) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
 (fp_rect (start -0.8 -0.4) (end 0.8 0.4) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))
 (fp_rect (start -1.3 -0.7) (end 1.3 0.7) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))
 (fp_line (start -0.25 -0.6) (end 0.25 -0.6) (stroke (width 0.12) (type default)) (layer "F.SilkS"))
 (fp_line (start -0.25 0.6) (end 0.25 0.6) (stroke (width 0.12) (type default)) (layer "F.SilkS"))
 (pad "1" smd rect (at -0.725 0) (size 0.65 0.9) (layers "F.Cu" "F.Paste" "F.Mask"))
 (pad "2" smd rect (at 0.725 0) (size 0.65 0.9) (layers "F.Cu" "F.Paste" "F.Mask")))\n''',encoding='utf8')
export('after')
from PIL import Image,ImageDraw
boxes={'usb5v_output':(100,230,232,284),'power_block':(16,169,232,286),'J2':(331,59,381,89)}
for v in ['before','after']:
 im=Image.open(H/v/'schematic.png').convert('RGB');f=im.width/(594/1.27)
 for name,b in boxes.items():im.crop(tuple(round(x*f) for x in b)).save(H/v/(name+'.png'))
 im.resize((1680,1188)).save(H/v/'overview.png')
ims=[Image.open(H/v/'usb5v_output.png') for v in ['before','after']];im=Image.new('RGB',(max(p.width for p in ims),sum(p.height for p in ims)+60),'white');d=ImageDraw.Draw(im);y=0
for title,p in zip(['Before fa741e9','After R-0016'],ims):d.text((10,y+5),title,fill='black');im.paste(p,(0,y+30));y+=p.height+30
im.save(H/'comparison.png')
print('Exported before/after; run verify.py and visual review before commit.')
