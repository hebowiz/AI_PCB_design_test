"""Local capacitor review edits, guarded against replay on edited source."""
from pathlib import Path
import os,sys,copy,uuid,subprocess,json,hashlib,datetime,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent; R=H.parents[1]; ROOT=R.parents[1]
sys.path.insert(0,str(R/'scripts'));from sexpr import *
BASE='16af1db20c48fef838b1d040675382488f75352e';REL='01_New_Design/kicad_direct/a2_usb_uart.kicad_sch';source=ROOT/REL
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
 export('before');s=parse(base.decode('utf-8-sig'));objs={ref(o):o for o in children(s,'symbol')}
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
 # C3 -> pin 12, C4 -> pin 24: separate local branches.
 for a,b in [((117,83),(122,83)),((122,83),(122,84)),((122,83),(137,83)),((122,90),(122,91)),((137,83),(137,84)),((137,83),(147,83)),((137,90),(137,91)),((147,81),(147,83)),((147,81),(153,81)),((147,83),(147,87)),((147,87),(153,87))]:cut(a,b)
 undot([(122,83),(137,83),(147,83)])
 move('C3',124,85);move('#PWR0151',124,89);move('C4',138,89);move('#PWR0152',138,93);labelpos('C4',135,89);move('#PWR0109',120,79)
 for a,b in [((120,79),(124,79)),((124,79),(124,81)),((124,81),(124,82)),((124,81),(153,81)),((124,88),(124,89)),((120,79),(120,86)),((120,86),(138,86)),((138,86),(143,86)),((143,86),(143,87)),((143,87),(153,87)),((138,92),(138,93))]:wire(a,b)
 for p in [(120,79),(124,81),(138,86)]:dot(*p)
 # Move only the RESET_N route to clear C4's lower GND, keeping endpoints.
 for a,b in [((45,132),(120,132)),((120,93),(120,132)),((120,93),(143,93)),((143,89),(143,93)),((143,89),(153,89))]:cut(a,b)
 for a,b in [((45,132),(118,132)),((118,96),(118,132)),((118,96),(145,96)),((145,89),(145,96)),((145,89),(153,89))]:wire(a,b)
 # VCCD C2/C5 bank and independent pin 46 branch C6.
 for a,b in [((110,98),(110,100)),((110,100),(110,102)),((110,100),(124,100)),((124,100),(124,102)),((124,100),(138,100)),((138,100),(138,102)),((138,100),(143,100)),((143,100),(143,107)),((143,107),(153,107)),((143,100),(149,100)),((149,100),(149,99)),((149,99),(151,99)),((110,108),(110,109)),((124,108),(124,109)),((138,108),(138,109))]:cut(a,b)
 undot([(110,100),(124,100),(138,100),(143,100)])
 move('C2',110,103);move('#PWR0150',110,107);labelpos('C2',107,103)
 move('C5',130,103);move('#PWR0153',130,107)
 move('C6',138,111);move('#PWR0154',138,115);labelpos('C6',135,111)
 move('#FLG07',141,100)
 newnum=max(int(r[4:]) for r in objs if r.startswith('#PWR'))+1
 clone('#PWR0172',f'#PWR{newnum:04}',134,108)
 for a,b in [((110,98),(110,100)),((110,100),(130,100)),((130,100),(141,100)),((141,100),(141,99)),((141,99),(151,99)),((110,106),(110,107)),((130,106),(130,107)),((134,108),(138,108)),((138,108),(143,108)),((143,108),(143,107)),((143,107),(153,107)),((138,114),(138,115))]:wire(a,b)
 # Cap top pins at y100 and y108 are direct junctions with named supply rails.
 for p in [(110,100),(130,100),(141,100),(138,108)]:dot(*p)
 # VREGIN: existing C1 bulk plus new C23 high-frequency decoupling.
 for a,b in [((146,101),(146,123)),((146,123),(150,123)),((150,123),(150,125)),((150,131),(150,132))]:cut(a,b)
 move('C1',150,134);move('#PWR0149',150,138);labelpos('C1',147,134);move('#PWR0174',150,129)
 clone('C5','C23',162,134);clone('#PWR0149',f'#PWR{newnum+1:04}',162,138)
 for a,b in [((146,101),(146,129)),((146,129),(150,129)),((150,129),(150,131)),((150,131),(162,131)),((150,137),(150,138)),((162,137),(162,138))]:wire(a,b)
 dot(150,131)
 # Select a 25 V, 0805, X5R part; DNP filter bulk follows the reference N.F.
 for rr in ['C1','C2','C11','C12']:
  o=objs[rr];prop(o,'Value')[2]=Q('4.7u');prop(o,'MPN')[2]=Q('CL21A475KAQNNNE');prop(o,'Footprint')[2]=Q('Capacitor_SMD:C_0805_2012Metric');prop(o,'Datasheet')[2]=Q('https://product.samsungsem.com/mlcc/CL21A475KAQNNN.do')
 for rr in ['C11','C12']:one(objs[rr],'dnp')[1]='yes'
 notes={'C1':'VREGIN pin 40 bulk, 4.7uF X5R 25V +/-10%; verify bias/ESR/start-up on PCB.',
 'C2':'VCCD pin 39 bulk, 4.7uF X5R 25V +/-10%; follows FT232H Fig 6.1 nominal value.',
 'C3':'100nF local decoupling for U1.12 VCCIO; place directly at this PCB pin.',
 'C4':'100nF local decoupling for U1.24 VCCIO; place directly at this PCB pin.',
 'C5':'100nF local decoupling for U1.39 VCCD; C2 is the parallel bulk capacitor.',
 'C6':'100nF local decoupling for U1.46 VCCIO; place directly at this PCB pin.',
 'C11':'DNP / N.F.: optional VPHY filter bulk per FT232H Fig 6.1; fit only after evaluation.',
 'C12':'DNP / N.F.: optional VPLL filter bulk per FT232H Fig 6.1; fit only after evaluation.',
 'C23':'100nF local decoupling for U1.40 VREGIN, parallel to C1; place directly at this PCB pin.'}
 for rr,txt in notes.items():prop(objs[rr],'Note')[2]=Q(txt)
 def txt(t,x,y,size=.9):s.append(['text',Q(t),['at',*pt(x,y),0],['effects',['font',['size',size,size]],['justify','left']],['uuid',uid()]])
 txt('C3 -> U1.12',124,92,.8);txt('C4 -> U1.24',128,94,.8)
 txt('C2 + C5 -> U1.39 (VCCD)',96,114,.8)
 txt('C6 -> U1.46',126,118,.8)
 txt('C1 + C23 -> U1.40 (VREGIN)',143,143,.8)
 txt('C11 / C12: 4.7uF N.F. (DNP); C9 / C10 remain fitted.',85,153,.8)
 replacements={'C9/C11 -> VPHY; C10/C12 -> VPLL. C3-C6 -> U1 3V3 pins.':'C3 / C4 / C6: 100nF at VCCIO 12 / 24 / 46. C2 + C5 at VCCD 39.',
 'USB5V -> U1.40 VREGIN; C1 is beside U1.':'USB5V -> U1.40 VREGIN; C1 4.7uF + C23 100nF.',
 'R-0004/5 revised; PCB/BOM not updated.':'R-0007/8 revised; PCB/BOM not updated.',
 'R-0004/5: human review pending. Not for fabrication.':'R-0007/8: human review pending. Not for fabrication.'}
 for t in children(s,'text'):
  if str(t[1]) in replacements:t[1]=Q(replacements[str(t[1])])
 # Visual pass 2: separate texts, supply symbols, and nearby ground triangles.
 for a,b in [((120,79),(124,79)),((124,79),(124,81)),((120,79),(120,86)),((120,86),(138,86))]:cut(a,b)
 undot([(120,79)])
 move('#PWR0109',108,86)
 for a,b in [((108,86),(116,86)),((116,86),(116,81)),((116,81),(124,81)),((116,86),(138,86))]:wire(a,b)
 dot(116,86)
 for name,yy in [('Reference',83),('Value',85)]:one(prop(objs['C3'],name),'at')[1:]=[*pt(127,yy),0]
 labelpos('C5',127,103)
 cut((134,108),(138,108));move('#PWR0175',138,106);wire((138,106),(138,108))
 p=prop(objs['#PWR0108'],'Value');one(p,'at')[1:]=[*pt(108,71),0];e=one(p,'effects');j=one(e,'justify')
 if j:j[1:]=['right']
 else:e.append(['justify','right'])
 for a,b in [((145,97),(145,116)),((136,116),(145,116)),((136,116),(136,118)),((136,124),(136,125))]:cut(a,b)
 move('C8',136,126);move('#PWR0104',136,121);move('#PWR0156',136,130)
 for a,b in [((145,97),(145,121)),((136,121),(145,121)),((136,121),(136,123)),((136,129),(136,130))]:wire(a,b)
 # Visual pass 3: remove a stale junction and clear C10 GND from the pin-12 rail.
 undot([(136,116)]);dot(136,121)
 labelpos('R1',103,87)
 for a,b in [((108,86),(116,86)),((116,86),(116,81)),((116,81),(124,81)),((116,86),(138,86)),((124,81),(153,81))]:cut(a,b)
 undot([(116,86)])
 for a,b in [((108,86),(128,86)),((128,86),(138,86)),((128,86),(128,81)),((124,81),(128,81)),((128,81),(153,81))]:wire(a,b)
 dot(128,86);dot(128,81)
 for name,yy in [('Reference',83),('Value',85)]:
  p=prop(objs['C3'],name);one(p,'at')[1:]=[*pt(121,yy),0];one(p,'effects').append(['justify','right']) if not one(one(p,'effects'),'justify') else None
  one(one(p,'effects'),'justify')[1:]=['right']
 for a,b in [((126,73),(126,74)),((126,80),(126,81))]:cut(a,b)
 undot([(126,73)]);dot(120,73)
 move('C10',120,77);move('#PWR0158',120,81)
 for a,b in [((120,73),(120,74)),((120,80),(120,81))]:wire(a,b)
 for t in children(s,'text'):
  if str(t[1])=='C6 -> U1.46':one(t,'at')[1:3]=pt(120,120)
 # Visual pass 4: keep the C12 value clear of C10 plates.
 for a,b in [((120,73),(120,74)),((120,80),(120,81))]:cut(a,b)
 undot([(120,73)]);dot(122,73)
 move('C10',122,77);move('#PWR0158',122,81)
 for a,b in [((122,73),(122,74)),((122,80),(122,81))]:wire(a,b)
 one(one(s,'title_block'),'rev')[1]=Q('A2-R0007-8 REVIEW')
 source.write_text(dump(s)+'\n',encoding='utf8')
export('after')
from PIL import Image,ImageDraw
boxes={'power_pins':(94,77,179,146),'phy_pll':(84,52,158,82),'ft232h':(80,52,190,157)}
for version in ['before','after']:
 im=Image.open(H/version/'schematic.png').convert('RGB');f=im.width/(594/1.27)
 for name,b in boxes.items():im.crop(tuple(round(x*f) for x in b)).save(H/version/(name+'.png'))
 im.resize((1680,1188)).save(H/version/'overview.png')
for name in boxes:
 ims=[Image.open(H/v/(name+'.png')) for v in ['before','after']];im=Image.new('RGB',(sum(i.width for i in ims),max(i.height for i in ims)+30),'white');d=ImageDraw.Draw(im);x=0
 for title,p in zip(['Before 16af1db','After R-0007/8'],ims):im.paste(p,(x,30));d.text((x+10,10),title,fill='black');x+=p.width
 im.save(H/('comparison_'+name+'.png'))
def pins(p):return {n.get('ref')+'.'+n.get('pin'):net.get('name') for net in ET.parse(p).findall('.//nets/net') for n in net.findall('node')}
def parts(p):return {e.get('ref'):e for e in ET.parse(p).findall('.//components/comp')}
a=pins(H/'before/netlist.xml');b=pins(H/'after/netlist.xml');ca=parts(H/'before/netlist.xml');cb=parts(H/'after/netlist.xml');sa=parse(base.decode('utf-8-sig'));sb=parse(source.read_text());oa={ref(o):o for o in children(sa,'symbol')};ob={ref(o):o for o in children(sb,'symbol')}
props=lambda o:{str(p[1]):str(p[2]) for p in children(o,'property')}
attrs={r:{k:[props(oa[r]).get(k),props(ob[r]).get(k)] for k in set(props(oa[r]))|set(props(ob[r])) if props(oa[r]).get(k)!=props(ob[r]).get(k)} for r in ca};attrs={r:v for r,v in attrs.items() if v}
allowed={r:{'Note'} for r in ['C3','C4','C5','C6']};allowed.update({r:{'Note','Value','MPN','Footprint','Datasheet'} for r in ['C1','C2','C11','C12']})
checks={'existing_terminal_nets_identical':all(b.get(k)==v for k,v in a.items()),'only_C23_new_terminals':set(b)-set(a)=={'C23.1','C23.2'} and b.get('C23.1')=='USB5V' and b.get('C23.2')=='GND','only_C23_added':set(cb)-set(ca)=={'C23'} and not(set(ca)-set(cb)),'only_approved_attributes_changed':all(r in allowed and set(v)<=allowed[r] for r,v in attrs.items()),'existing_UUIDs_unchanged':all(one(oa[r],'uuid')==one(ob[r],'uuid') for r in ca),'libraries_unchanged':one(sa,'lib_symbols')==one(sb,'lib_symbols'),'DNP_only_C11_C12':{r for r in ca if one(oa[r],'dnp')!=one(ob[r],'dnp')}=={'C11','C12'} and all(one(ob[r],'dnp')[1]=='yes' for r in ['C11','C12']),'VCCD_matches_reference':props(ob['C2'])['Value']=='4.7u' and props(ob['C5'])['Value']=='100n','VCCIO_three_100n':all(props(ob[r])['Value']=='100n' and b[r+'.1']=='+3V3' for r in ['C3','C4','C6']),'VREGIN_matches_reference':props(ob['C1'])['Value']=='4.7u' and props(ob['C23'])['Value']=='100n','caps_vertical':all(float(one(ob[r],'at')[3])==0 for r in ['C1','C2','C3','C4','C5','C6','C11','C12','C23'])}
for v in ['before','after']:
 er=json.loads((H/v/'erc.json').read_text());checks[v+'_ERC_zero']=not[i for sh in er['sheets'] for i in sh['violations']]
checks['ERC_config_unchanged']=json.loads((H/'before/erc.json').read_text())['ignored_checks']==json.loads((H/'after/erc.json').read_text())['ignored_checks']
basefiles=set(git('ls-tree','-r','--name-only',BASE).decode().splitlines());allchanged=git('diff','--name-only',BASE).decode().splitlines();changed=[f for f in allchanged if f in basefiles];checks['only_existing_schematic_changed']=changed==[REL] and all(f in basefiles or f.startswith('01_New_Design/kicad_direct/reports/review_capacitors/') for f in allchanged)
footprint=Path(os.environ['LOCALAPPDATA'])/'Programs/KiCad/10.0/share/kicad/footprints/Capacitor_SMD.pretty/C_0805_2012Metric.kicad_mod';checks['selected_footprint_installed']=footprint.exists()
report={'timestamp':datetime.datetime.now().astimezone().isoformat(),'base':BASE,'checks':checks,'all_pass':all(checks.values()),'components':[len(ca),len(cb)],'terminals':[len(a),len(b)],'nets':[len(set(a.values())),len(set(b.values()))],'attribute_delta':attrs,'terminal_delta':{k:[a.get(k),b.get(k)] for k in set(a)|set(b) if a.get(k)!=b.get(k)},'modified_existing_files':changed,'protected_existing_files':len(git('ls-tree','-r','--name-only',BASE,'01_New_Design/kicad_direct').decode().splitlines())-1,'source_sha256':sha(source.read_bytes()),'pin_assignments':{'C3':'U1.12','C4':'U1.24','C6':'U1.46','C2+C5':'U1.39','C1+C23':'U1.40'}}
(H/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(H/'export_manifest.json').write_text(json.dumps({str(p.relative_to(H)):sha(p.read_bytes()) for v in ['before','after'] for p in (H/v).iterdir() if p.is_file()},indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2));assert report['all_pass']
