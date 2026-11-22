"""Local schematic review edits, guarded against replay on edited source."""
from pathlib import Path
import os,sys,copy,uuid,subprocess,json,hashlib,datetime,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent; R=H.parents[1]; ROOT=R.parents[1]
sys.path.insert(0,str(R/'scripts'));from sexpr import *
BASE='7f0941b45309ad069e947849772c3ecf7c1d1e61';REL='01_New_Design/kicad_direct/a2_usb_uart.kicad_sch';source=ROOT/REL
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
 assert source.read_bytes()==base,'Refuse to replay on edited schematic'
 export('before');s=parse(base.decode('utf8'));objs={ref(o):o for o in children(s,'symbol')}
 def move(r,x,y):
  o=objs[r];a=one(o,'at');dx,dy=mm(x)-float(a[1]),mm(y)-float(a[2]);a[1:3]=pt(x,y)
  for p in children(o,'property'):
   a=one(p,'at');a[1]=round(float(a[1])+dx,5);a[2]=round(float(a[2])+dy,5)
 def cut(a,b):
  found=[w for w in children(s,'wire') if {tuple(map(float,p[1:3])) for p in one(w,'pts')[1:]}=={tuple(pt(*a)),tuple(pt(*b))}]
  assert len(found)==1,(a,b);s.remove(found[0])
 def wire(a,b):s.append(['wire',['pts',['xy',*pt(*a)],['xy',*pt(*b)]],['stroke',['width',0.1524],['type','default']],['uuid',uid()]])
 for a,b in [((45,120),(45,123)),((45,129),(45,132)),((45,132),(45,133)),((45,139),(45,140)),((45,132),(118,132)),((118,96),(118,132)),((118,96),(145,96))]:cut(a,b)
 move('R2',118,89);one(objs['R2'],'at')[3]=90
 move('C22',126,93);move('#PWR0102',110,89);move('#PWR0170',126,97)
 for name,y in [('Reference',85.5),('Value',87)]:
  p=prop(objs['R2'],name);one(p,'at')[1:]=[*pt(118,y),90];e=one(p,'effects');j=one(e,'justify')
  if j:e.remove(j)
 for name,y in [('Reference',92),('Value',94)]:
  p=prop(objs['C22'],name);one(p,'at')[1:]=[*pt(123,y),0];one(one(p,'effects'),'justify')[1:]=['right']
 for a,b in [((110,89),(115,89)),((121,89),(126,89)),((126,89),(126,90)),((126,96),(126,97)),((126,89),(129,89)),((129,89),(129,96)),((129,96),(145,96))]:wire(a,b)
 for j in children(s,'junction'):
  if list(map(float,one(j,'at')[1:3]))==pt(45,132):one(j,'at')[1:3]=pt(126,89)
 for l in children(s,'label'):
  if str(l[1])=='RESET_N':one(l,'at')[1:3]=pt(130,96)
 for t in children(s,'text'):
  if str(t[1])=='C3 -> U1.12':one(t,'at')[1:3]=pt(135,80)
  if str(t[1])=='C4 -> U1.24':one(t,'at')[1:3]=pt(134,94)
 for r in ['#FLG05','#FLG06']:one(objs[r],'at')[3]=0
 for t in children(s,'text'):
  if str(t[1]).startswith('R-0009..13'):t[1]=Q(str(t[1]).replace('R-0009..13','R-0014/15'))
 source.write_text(dump(s)+'\n',encoding='utf8')
export('after')
from PIL import Image,ImageDraw
boxes={'reset':(96,70,181,119),'flags':(128,178,169,253),'reset_before_context':(32,75,182,148)}
for v in ['before','after']:
 im=Image.open(H/v/'schematic.png').convert('RGB');f=im.width/(594/1.27)
 for name,b in boxes.items():im.crop(tuple(round(x*f) for x in b)).save(H/v/(name+'.png'))
 im.resize((1680,1188)).save(H/v/'overview.png')
for name in boxes:
 ims=[Image.open(H/v/(name+'.png')) for v in ['before','after']];im=Image.new('RGB',(sum(p.width for p in ims),max(p.height for p in ims)+30),'white');d=ImageDraw.Draw(im);x=0
 for title,p in zip(['Before 7f0941b','After R-0014/15'],ims):im.paste(p,(x,30));d.text((x+10,10),title,fill='black');x+=p.width
 im.save(H/('comparison_'+name+'.png'))
def pins(p):return {n.get('ref')+'.'+n.get('pin'):net.get('name') for net in ET.parse(p).findall('.//nets/net') for n in net.findall('node')}
def parts(p):return {e.get('ref'):e for e in ET.parse(p).findall('.//components/comp')}
a=pins(H/'before/netlist.xml');b=pins(H/'after/netlist.xml');ca=parts(H/'before/netlist.xml');cb=parts(H/'after/netlist.xml')
sa=parse(base.decode('utf8'));sb=parse(source.read_text());oa={ref(o):o for o in children(sa,'symbol')};ob={ref(o):o for o in children(sb,'symbol')}
props=lambda o:{str(p[1]):str(p[2]) for p in children(o,'property')}
checks={'all_terminal_nets_identical':a==b,'all_real_parts_identical':set(ca)==set(cb),'all_real_attributes_identical':all(props(oa[r])==props(ob[r]) for r in ca),'all_original_symbol_UUIDs_preserved':all(one(oa[r],'uuid')==one(ob[r],'uuid') for r in oa),'symbol_definitions_identical':one(sa,'lib_symbols')==one(sb,'lib_symbols'),'DNP_and_BOM_flags_identical':all(all(one(oa[r],k)==one(ob[r],k) for k in ['dnp','in_bom','on_board']) for r in oa),'all_symbol_references_identical':set(ob)==set(oa)}
for v in ['before','after']:
 er=json.loads((H/v/'erc.json').read_text());checks[v+'_ERC_zero']=not [i for sh in er['sheets'] for i in sh['violations']]
checks['ERC_config_unchanged']=json.loads((H/'before/erc.json').read_text())['ignored_checks']==json.loads((H/'after/erc.json').read_text())['ignored_checks']
basefiles=set(git('ls-tree','-r','--name-only',BASE).decode().splitlines());allchanged=git('diff','--name-only',BASE).decode().splitlines();changed=[f for f in allchanged if f in basefiles];checks['protected_files_unchanged']=changed==[REL] and all(f in basefiles or f.startswith('01_New_Design/kicad_direct/reports/review_reset_flags/') for f in allchanged)
report={'timestamp':datetime.datetime.now().astimezone().isoformat(),'base':BASE,'checks':checks,'all_pass':all(checks.values()),'components':[len(ca),len(cb)],'terminals':[len(a),len(b)],'nets':[len(set(a.values())),len(set(b.values()))],'terminal_delta':{k:[a.get(k),b.get(k)] for k in set(a)|set(b) if a.get(k)!=b.get(k)},'modified_existing_files':changed,'source_sha256':sha(source.read_bytes())}
(H/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(H/'export_manifest.json').write_text(json.dumps({str(p.relative_to(H)):sha(p.read_bytes()) for v in ['before','after'] for p in (H/v).iterdir() if p.is_file()},indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2));assert report['all_pass']

def canonical(v):
 x=ET.parse(H/v/'netlist.xml')
 def node(e):return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),sorted([node(c) for c in e],key=repr)]
 return {'components':sorted([node(e) for e in x.findall('.//components/comp')],key=repr),'libparts':sorted([node(e) for e in x.findall('.//libparts/libpart')],key=repr),'nets':{e.get('name'):sorted([sorted(n.attrib.items()) for n in e.findall('node')],key=repr) for e in x.findall('.//nets/net')}}
nets_a,nets_b=canonical('before'),canonical('after')
for v,data in [('before',nets_a),('after',nets_b)]:(H/('canonical_netlist_'+v+'.json')).write_text(json.dumps(data,indent=2))
checks['canonical_netlists_identical']=nets_a==nets_b
checks['all_FLAGs_up']=all(float(one(o,'at')[3])==0 and one(o,'mirror') is None for r,o in ob.items() if r.startswith('#FLG'))
checks['FLAG_connection_points_preserved']=all(one(oa[r],'at')[1:3]==one(ob[r],'at')[1:3] for r in ['#FLG05','#FLG06'])
allowed={'R2','C22','#PWR0102','#PWR0170','#FLG05','#FLG06'}
checks['unrelated_symbols_identical']=all(oa[r]==ob[r] for r in oa if r not in allowed)
report['checks']=checks;report['all_pass']=all(checks.values())
report['geometry']={'R2_to_U1_34_horizontal_mm':[137.16,44.45],'C22_to_U1_34_horizontal_mm':[137.16,34.29],'FLAG_count':7,'downward_FLAGs_before':['#FLG05','#FLG06'],'downward_FLAGs_after':[]}
(H/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2));assert report['all_pass']

manifest=json.loads((H/'export_manifest.json').read_text())
checks['export_hashes_match']=all(sha((H/p).read_bytes())==v for p,v in manifest.items())
checks['source_matches_export']=source.read_bytes()==(H/'after/a2_usb_uart.kicad_sch').read_bytes()
report['protected_existing_A2_file_count']=len([p for p in basefiles if p.startswith('01_New_Design/kicad_direct/')])-1
report['all_pass']=all(checks.values());(H/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');assert report['all_pass']
