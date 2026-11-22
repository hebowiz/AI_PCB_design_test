"""Targeted R-0004/5 follow-up edits. Does not run any original generator.
Run once to patch exact 3b8700a baseline; --export-after only reexports/rechecks.
"""
from pathlib import Path
import os,sys,copy,uuid,subprocess,json,hashlib,datetime,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent; R=H.parents[1]; ROOT=R.parents[1]
sys.path.insert(0,str(R/'scripts'));from sexpr import *
BASE='3b8700a24ef3cee159253b8f21e5b9d400c67a10';REL='01_New_Design/kicad_direct/a2_usb_uart.kicad_sch';source=ROOT/REL
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
 assert source.read_bytes()==base,'Source edited; refuse patch'
 export('before');s=parse(base.decode('utf-8-sig'));objs={ref(o):o for o in children(s,'symbol')}
 def move(r,x,y):
  o=objs[r];ox,oy=map(float,one(o,'at')[1:3]);nx,ny=pt(x,y);one(o,'at')[1:3]=[nx,ny]
  for p in children(o,'property'):
   a=one(p,'at');a[1]=round(float(a[1])+nx-ox,5);a[2]=round(float(a[2])+ny-oy,5)
 def wire(a,b):s.append(['wire',['pts',['xy',*pt(*a)],['xy',*pt(*b)]],['stroke',['width',0.1524],['type','default']],['uuid',uid()]])
 def cut(a,b):
  m=[w for w in children(s,'wire') if {tuple(map(float,p[1:])) for p in one(w,'pts')[1:]}=={tuple(pt(*a)),tuple(pt(*b))}]
  assert len(m)==1,(a,b);s.remove(m[0])
 def dot(x,y):s.append(['junction',['at',*pt(x,y)],['diameter',0.762],['color',0,0,0,0],['uuid',uid()]])
 # Clear only old C1/C2 drawing connections; retain the USB5V trunk.
 for w in children(s,'wire'):
  ps=[tuple(float(v)/1.27 for v in p[1:]) for p in one(w,'pts')[1:]]
  if all(23.99<=x<=106.01 and 184.99<=y<=194.01 for x,y in ps):s.remove(w)
 for j in children(s,'junction'):
  x,y=[float(v)/1.27 for v in one(j,'at')[1:3]]
  if abs(x-24)<.01 and abs(y-185)<.01:s.remove(j)
 move('C1',150,128);move('#PWR0149',150,132);move('C2',138,105);move('#PWR0150',138,109)
 move('C5',110,105);move('#PWR0153',110,109);move('C6',124,105);move('#PWR0154',124,109);move('#PWR0172',110,98)
 for name,y in [('Reference',104),('Value',106)]:
  p=prop(objs['C2'],name);one(p,'at')[1:]=[*pt(135,y),0];one(one(p,'effects'),'justify')[1:]=['right']
 # Exact old 3V3 decoupling rail and drops.
 for a,b in [((124,99),(124,101)),((124,101),(124,102)),((124,101),(137,101)),((137,101),(137,102)),((137,101),(143,101)),((143,101),(143,107)),((124,108),(124,109)),((137,108),(137,109))]:cut(a,b)
 for j in children(s,'junction'):
  xy=tuple(round(float(v)/1.27,5) for v in one(j,'at')[1:3])
  if xy in [(124,101),(137,101),(143,101)]:s.remove(j)
 for a,b in [((110,98),(110,100)),((110,100),(110,102)),((110,100),(124,100)),((124,100),(124,102)),((124,100),(138,100)),((138,100),(138,102)),((138,100),(143,100)),((143,100),(143,107)),((143,100),(149,100)),((149,100),(149,99)),((149,99),(151,99)),((110,108),(110,109)),((124,108),(124,109)),((138,108),(138,109)),((151,101),(146,101)),((146,101),(146,123)),((146,123),(150,123)),((150,123),(150,125)),((150,131),(150,132))]:wire(a,b)
 for xy in [(110,100),(124,100),(138,100),(143,100)]:dot(*xy)
 for g in children(s,'global_label'):
  assert g[1] in ('USB5V','+3V3');s.remove(g)
 # Reuse the existing VCCD drive flag on the new local output rail.
 f=next(o for o in children(s,'symbol') if ref(o).startswith('#FLG') and tuple(map(float,one(o,'at')[1:3]))==tuple(pt(88,185)))
 move(ref(f),143,100)
 s.remove(objs['#PWR0119'])
 p=copy.deepcopy(objs['#PWR0101']);new='#PWR'+str(max(int(r[4:]) for r in objs if r.startswith('#PWR'))+1).zfill(4)
 prop(p,'Reference')[2]=Q(new);one(p,'uuid')[1]=uid()
 for pin in children(p,'pin'):one(pin,'uuid')[1]=uid()
 for pr in children(one(p,'instances'),'project'):
  for pa in children(pr,'path'):one(pa,'reference')[1]=Q(new)
 objs[new]=p;s.append(p);move(new,150,123)
 v=prop(p,'Value');one(v,'at')[1:]=[mm(150),round(mm(123)-4.5,5),0];e=one(v,'effects');j=one(e,'justify')
 if j:e.remove(j)
 prop(objs['C1'],'Note')[2]=Q('USB5V input bypass at U1.40 VREGIN; maintain effective capacitance at DC bias.')
 prop(objs['C2'],'Note')[2]=Q('+3V3 output bypass at U1.39 VCCD; verify effective capacitance and transients.')
 # Remove U6 and its dedicated QOD/input/output components. Keep shared U4 control.
 for r in ['U6','R16','C20','C21','#PWR0122','#PWR0139','#PWR0168','#PWR0169']:s.remove(objs[r])
 for w in children(s,'wire'):
  ps=[tuple(map(float,p[1:])) for p in one(w,'pts')[1:]]
  if all(y>=370.83 and x<=217.18 for x,y in ps):s.remove(w)
 for typ in ['junction','label','no_connect']:
  for o in children(s,typ):
   x,y=map(float,one(o,'at')[1:3])
   if y>=370.83 and x<217.16:s.remove(o)
 for a,b in [((24,292),(160,292)),((160,292),(160,294)),((160,294),(171,294))]:wire(a,b)
 replacement={
 '04  POWER: U1 INTERNAL 3V3 / U4 VIO / U6 SWITCHED 5V':'04  POWER: U1 INTERNAL 3V3 / U4 VIO / MANUAL 5V',
 'U3 removed. USB5V -> U1.40 VREGIN (see block 01).':'USB5V -> U1.40 VREGIN; C1 is beside U1.',
 'U1.39 VCCD -> +3V3 -> U1 / U2 VCCA / EEPROM / control.':'U1.39 VCCD -> C2 / +3V3 -> bridge / EEPROM / control.',
 '3V3 flag declares U1.39 output with VREGIN=5V.':'U1.39 output is declared by a flag in block 01.',
 'C1/C2 retained: place near U1 in PCB update.':'C1/C2 connections are drawn at U1. PCB update pending.',
 'U6: USB 5V load switch. R16 discharges OUT via QOD; SW2 controls the header.':'USB5V -> SW2 -> USB5V_OUT. Manual output, independent of USB configuration / suspend.',
 'USB5V -> U6 -> USB5V_ENABLED -> SW2 -> USB5V_OUT':'USB5V -> SW2 -> USB5V_OUT (manual only)',
 'PWR_EN enables U4 and U6 in parallel.':'PWR_EN enables U4. U6 / R16 / C20 / C21 removed.',
 'R-0001 retained; R-0002/3/4 revised. PCB/BOM not updated.':'R-0004/5 revised; PCB/BOM not updated.',
 'R-0002/3/4: human review pending. Not for fabrication.':'R-0004/5: human review pending. Not for fabrication.'}
 for t in children(s,'text'):
  if str(t[1]) in ['USB5V bulk','VCCD bulk (U1.39 output)']:s.remove(t)
  elif str(t[1]) in replacement:t[1]=Q(replacement[str(t[1])])
 one(one(s,'title_block'),'rev')[1]=Q('A2-R0004-5 REVIEW')
 source.write_text(dump(s)+'\n',encoding='utf8')
export('after')
from PIL import Image,ImageDraw
boxes={'ft232h_power':(99,88,179,133),'manual_5v':(16,282,224,320),'leds':(389,30,463,119),'clock':(85,25,150,65)}
for v in ('before','after'):
 im=Image.open(H/v/'schematic.png').convert('RGB');f=im.width/(594/1.27)
 for n,b in boxes.items():im.crop(tuple(round(c*f) for c in b)).save(H/v/(n+'.png'))
 im.resize((1680,1188)).save(H/v/'overview.png')
for n in boxes:
 pics=[Image.open(H/v/(n+'.png')) for v in ('before','after')];c=Image.new('RGB',(sum(p.width for p in pics),max(p.height for p in pics)+30),'white');d=ImageDraw.Draw(c);x=0
 for title,p in zip(('Before 3b8700a','After R-0004/5'),pics):c.paste(p,(x,30));d.text((x+10,10),title,fill='black');x+=p.width
 c.save(H/('comparison_'+n+'.png'))
def pins(p):return {n.get('ref')+'.'+n.get('pin'):net.get('name') for net in ET.parse(p).findall('.//nets/net') for n in net.findall('node')}
def comps(p):return {e.get('ref'):e for e in ET.parse(p).findall('.//components/comp')}
a=pins(H/'before/netlist.xml');b=pins(H/'after/netlist.xml');removed={'U6','R16','C20','C21'};expected={k:('USB5V' if v=='USB5V_ENABLED' else v) for k,v in a.items() if k.split('.')[0] not in removed}
ca=comps(H/'before/netlist.xml');cb=comps(H/'after/netlist.xml');sa=parse(base.decode('utf-8-sig'));sb=parse(source.read_text());oa={ref(o):o for o in children(sa,'symbol')};ob={ref(o):o for o in children(sb,'symbol')}
props=lambda o:{str(p[1]):str(p[2]) for p in children(o,'property')}
attrs={r:{k:[props(oa[r])[k],props(ob[r])[k]] for k in props(oa[r]) if props(oa[r])[k]!=props(ob[r])[k]} for r in cb};attrs={r:v for r,v in attrs.items() if v}
checks={'only_expected_terminal_delta':b==expected,'only_dedicated_parts_removed':set(ca)-set(cb)==removed and not(set(cb)-set(ca)),'only_C1_C2_note_properties_changed':all(r in ['C1','C2'] and set(v)=={'Note'} for r,v in attrs.items()),'all_libraries_unchanged':one(sa,'lib_symbols')==one(sb,'lib_symbols'),'remaining_UUIDs_unchanged':all(one(oa[r],'uuid')==one(ob[r],'uuid') for r in cb),'R1_R2_R3_R6_and_shared_control_unchanged':all(oa[r]==ob[r] for r in ['D1','D5','Y1','C13','C14','D2','D3','D4','R13','R14','R15','U5','R3','R4','Q1','R5','R6','U4','SW2']),'no_global_label_connectors':not children(sb,'global_label'),'input_output_power_nets_separate':b['U1.40']==b['C1.1']=='USB5V' and b['U1.39']==b['C2.1']=='+3V3','manual_switch_input_USB5V':b['SW2.3']=='USB5V','C1_C2_vertical_and_GND_lower':all(float(one(ob[r],'at')[3])==0 and b[r+'.2']=='GND' for r in ['C1','C2'])}
for v in ['before','after']:
 er=json.loads((H/v/'erc.json').read_text());checks[v+'_ERC_zero']=not [i for sh in er['sheets'] for i in sh['violations']]
checks['ERC_config_unchanged']=json.loads((H/'before/erc.json').read_text())['ignored_checks']==json.loads((H/'after/erc.json').read_text())['ignored_checks']
changed=git('diff','--name-only','--diff-filter=MDT',BASE).decode().splitlines();checks['only_existing_schematic_changed']=changed==[REL]
# Git-aware comparison handles CRLF without one process per file.
oldpaths=set(git('ls-tree','-r','--name-only',BASE,'01_New_Design/kicad_direct').decode().splitlines())-{REL};altered=set(changed)
checks['existing_A2_files_protected']=not(oldpaths & altered)
report=dict(checks=checks,all_pass=all(checks.values()),base=BASE,timestamp=datetime.datetime.now().astimezone().isoformat(),components=[len(ca),len(cb)],terminals=[len(a),len(b)],nets=[len(set(a.values())),len(set(b.values()))],terminal_delta={k:{'before':a.get(k),'after':b.get(k)} for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)},attribute_delta=attrs,protected_count=len(oldpaths),modified_existing_files=changed,source_sha256=sha(source.read_bytes()))
(H/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(H/'export_manifest.json').write_text(json.dumps({str(p.relative_to(H)):sha(p.read_bytes()) for v in ['before','after'] for p in (H/v).iterdir() if p.is_file()},indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2));assert report['all_pass']
