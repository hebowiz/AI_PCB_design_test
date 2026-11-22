"""R-0001 targeted ESD substitution, exports, and explicit expected-delta checks.
Never run a previous design/layout generator. Refuse to overwrite unrecorded edits.
"""
from pathlib import Path
import os,sys,copy,uuid,subprocess,json,hashlib,datetime,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent; R=H.parents[1]; ROOT=R.parents[1]
sys.path.insert(0,str(R/'scripts'));from sexpr import *
BASE='778ab8896a4f9b71efba0c45f701cbf2fdfc2cac'
REL='01_New_Design/kicad_direct/a2_usb_uart.kicad_sch'; source=ROOT/REL
cli=Path(os.environ['LOCALAPPDATA'])/'Programs/KiCad/10.0/bin/kicad-cli.exe'
share=cli.parents[1]/'share/kicad'
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
def uid():return Q(str(uuid.uuid4()))
def ref(o):return str(next(p[2] for p in children(o,'property') if p[1]=='Reference'))
def prop(o,n):return next(p for p in children(o,'property') if p[1]==n)
def mm(x):return round(x*1.27,5)
def point(x,y):return [mm(x),mm(y)]
log=json.loads((H/'commands.json').read_text()) if '--export-after' in sys.argv and (H/'commands.json').exists() else []
def run(cmd):
 p=subprocess.run(list(map(str,cmd)),cwd=ROOT,capture_output=True)
 log.append({'at':datetime.datetime.now().astimezone().isoformat(),'command':list(map(str,cmd)),'exit_code':p.returncode,'stdout':p.stdout.decode('utf8','replace'),'stderr':p.stderr.decode('utf8','replace')})
 (H/'commands.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf8')
 if p.returncode:raise RuntimeError(log[-1])
def export(version):
 out=H/version;out.mkdir(exist_ok=True)
 for args,name in [(['export','netlist','--format','kicadxml'],'netlist.xml'),(['erc','--format','json','--exit-code-violations'],'erc.json'),(['export','pdf','--black-and-white'],'schematic.pdf')]:
  run([cli,'sch',*args,'-o',out/name,source])
 run(['pdftoppm','-scale-to','5600','-png','-singlefile',out/'schematic.pdf',out/'schematic'])
 (out/'manifest.json').write_text(json.dumps({'source_sha256':sha(source.read_bytes()),'files':{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.name in ('a2_usb_uart.kicad_sch','netlist.xml','erc.json','schematic.pdf','schematic.png')}},indent=2))
base=git('show',BASE+':'+REL)
if '--export-after' not in sys.argv:
 assert source.read_bytes()==base,'Source differs from V3-polish; refusing overwrite'
 (H/'before').mkdir(exist_ok=True);(H/'before/a2_usb_uart.kicad_sch').write_bytes(base)
 export('before')
 s=parse(base.decode('utf-8-sig')); libs=one(s,'lib_symbols'); objs={ref(o):o for o in children(s,'symbol')}
 assert 'D5' not in objs
 d=objs['D1'];old=copy.deepcopy(d);g=objs['#PWR0141']
 standard=parse((share/'symbols/Device.kicad_sym').read_text(encoding='utf-8-sig'))
 lib=copy.deepcopy(next(o for o in children(standard,'symbol') if o[1]=='D_Zener'))
 lib[1]=Q('Device:D_Zener');libs.append(lib)
 # K=pin1, A=pin2 matches ESD321 DPY IO=1 / GND=2. Do not use bidirectional D_TVS.
 footprint='Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm'
 assert (share/'footprints/Package_SON.pretty'/ (footprint.split(':')[1]+'.kicad_mod')).exists()
 def diode(o,name,x,y,new=False):
  one(o,'lib_id')[1]=Q('Device:D_Zener');one(o,'at')[1:]=[*point(x,y),270]
  if new:one(o,'uuid')[1]=uid()
  values={'Reference':name,'Value':'ESD321DPYR','MPN':'ESD321DPYR','Footprint':footprint,'Datasheet':'https://www.ti.com/lit/ds/symlink/esd321.pdf','Note':'Unidirectional USB ESD; DPY pin 1=IO(K), pin 2=GND(A); R-0001'}
  for p in children(o,'property'):
   p[2]=Q(values[str(p[1])]);one(p,'at')[1:]=[*point(x,y),0]
   if p[1] in ('Reference','Value'):
    one(p,'at')[1:]=[*point(x+8,y-1 if p[1]=='Reference' else y+1),90]
    e=one(p,'effects');j=one(e,'justify')
    if j:e.remove(j)
  for p in children(o,'pin'):o.remove(p)
  for n in ('1','2'):o.append(['pin',Q(n),['uuid',uid()]])
  for pr in children(one(o,'instances'),'project'):
   for pa in children(pr,'path'):one(pa,'reference')[1]=Q(name)
 diode(d,'D1',58,53)
 d5=copy.deepcopy(old);diode(d5,'D5',74,51,True);s.append(d5)
 def moveground(o,name,x,y,new=False):
  ox,oy=map(float,one(o,'at')[1:3]);nx,ny=point(x,y)
  one(o,'at')[1:3]=[nx,ny];prop(o,'Reference')[2]=Q(name)
  for p in children(o,'property'):
   at=one(p,'at');at[1]=round(float(at[1])+nx-ox,5);at[2]=round(float(at[2])+ny-oy,5)
  if new:
   one(o,'uuid')[1]=uid()
   for p in children(o,'pin'):one(p,'uuid')[1]=uid()
  for pr in children(one(o,'instances'),'project'):
   for pa in children(pr,'path'):one(pa,'reference')[1]=Q(name)
 newref='#PWR'+str(max(int(r[4:]) for r in objs if r.startswith('#PWR'))+1).zfill(4)
 g2=copy.deepcopy(g);moveground(g,'#PWR0141',58,57);moveground(g2,newref,74,55,True);s.append(g2)
 oldedges=[((58,48),(58,54)),((74,46),(74,54)),((66,62),(66,63))]
 removed=[]
 for w in children(s,'wire'):
  pts=one(w,'pts');e={tuple(map(float,p[1:])) for p in pts[1:]}
  if any(e=={tuple(point(*a)),tuple(point(*b))} for a,b in oldedges):s.remove(w);removed.append(str(one(w,'uuid')[1]))
 assert len(removed)==3
 for a,b in [((58,48),(58,50)),((58,56),(58,57)),((74,46),(74,48)),((74,54),(74,55))]:
  s.append(['wire',['pts',['xy',*point(*a)],['xy',*point(*b)]],['stroke',['width',0.1524],['type','default']],['uuid',uid()]])
 for t in children(s,'text'):
  if str(t[1]) in {'Existing part / pin identities and circuit are retained.': 'R-0001: D1/D5 ESD321DPYR; PCB/BOM not updated.', 'V3 polish. Candidate for human review; not approved.': 'R-0001 schematic. Human review pending; not approved.'}:t[1]=Q({'Existing part / pin identities and circuit are retained.': 'R-0001: D1/D5 ESD321DPYR; PCB/BOM not updated.', 'V3 polish. Candidate for human review; not approved.': 'R-0001 schematic. Human review pending; not approved.'}[str(t[1])])
 one(one(s,'title_block'),'rev')[1]=Q('A2-R0001 REVIEW')
 source.write_text(dump(s)+'\n',encoding='utf8')
 (H/'patch.json').write_text(json.dumps({'base':BASE,'before_sha256':sha(base),'after_sha256':sha(source.read_bytes()),'new_reference':'D5','new_ground_reference':newref,'removed_wire_uuids':removed,'footprint':footprint,'symbol':'Device:D_Zener','pin_mapping':{'D1.1':'USB_D+','D1.2':'GND','D5.1':'USB_D-','D5.2':'GND'}},indent=2))
export('after')
from PIL import Image,ImageDraw
for v in ('before','after'):
 im=Image.open(H/v/'schematic.png').convert('RGB');f=im.width/(594/1.27)
 im.crop(tuple(round(c*f) for c in (15,25,101,70))).save(H/v/'usb_detail.png')
 im.resize((1680,1188)).save(H/v/'overview.png')
pics=[Image.open(H/v/'usb_detail.png') for v in ('before','after')]
can=Image.new('RGB',(sum(p.width for p in pics),max(p.height for p in pics)+30),'white');draw=ImageDraw.Draw(can);x=0
for label,p in zip(('V3-polish: before','R-0001: ESD321DPYR x2'),pics):can.paste(p,(x,30));draw.text((x+10,10),label,fill='black');x+=p.width
can.save(H/'comparison_usb.png')
def comp(path):return {e.get('ref'):ET.tostring(e,encoding='unicode') for e in ET.parse(path).findall('.//components/comp')}
def pins(path):return {n.get('ref')+'.'+n.get('pin'):net.get('name') for net in ET.parse(path).findall('.//nets/net') for n in net.findall('node')}
a=pins(H/'before/netlist.xml');b=pins(H/'after/netlist.xml');expected=dict(a)
dm=expected.pop('D1.2');gn=expected.pop('D1.3');expected['D1.2']=gn;expected['D5.1']=dm;expected['D5.2']=gn
ca=comp(H/'before/netlist.xml');cb=comp(H/'after/netlist.xml')
sa=parse(base.decode('utf-8-sig'));sb=parse(source.read_text());oa={ref(o):o for o in children(sa,'symbol')};ob={ref(o):o for o in children(sb,'symbol')}
checks={'terminal_nets_exact_expected_delta':expected==b,'real_component_count_58_to_59':len(ca)==58 and len(cb)==59,'only_new_real_reference_D5':set(cb)-set(ca)=={'D5'} and not(set(ca)-set(cb)), 'all_other_component_XML_attributes_equal':all(ca[r]==cb[r] for r in ca if r!='D1'),'all_other_symbols_exactly_preserved':all(oa[r]==ob[r] for r in oa if r not in ('D1','#PWR0141')),'D1_symbol_uuid_preserved':one(oa['D1'],'uuid')==one(ob['D1'],'uuid'),'existing_library_definitions_preserved':all(x in children(one(sb,'lib_symbols'),'symbol') for x in children(one(sa,'lib_symbols'),'symbol')),'net_names_unchanged':set(a.values())==set(b.values()),'ERC_settings_unchanged':True}
for v in ('before','after'):
 er=json.loads((H/v/'erc.json').read_text());viol=[i for sh in er['sheets'] for i in sh['violations']]
 checks[v+'_ERC_zero_violations']=not viol
checks['ERC_settings_unchanged']=json.loads((H/'before/erc.json').read_text())['ignored_checks']==json.loads((H/'after/erc.json').read_text())['ignored_checks']
changed=git('diff','--name-only',BASE).decode().splitlines()
checks['only_existing_schematic_changed']=changed==[REL]
checks['unit1_pin1_cathode_pin2_anode']=True # symbol loaded verbatim from KiCad; inspect pin metadata below
for refname in ['D1','D5']:
 checks[refname+'_attributes']=all(str(prop(ob[refname],k)[2])==v for k,v in {'Value':'ESD321DPYR','MPN':'ESD321DPYR','Footprint':'Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm'}.items())
lib=next(l for l in children(one(sb,'lib_symbols'),'symbol') if l[1]=='Device:D_Zener')
ps={str(one(p,'number')[1]):str(one(p,'name')[1]) for u in children(lib,'symbol') for p in children(u,'pin')}
checks['unit1_pin1_cathode_pin2_anode']=ps=={'1':'K','2':'A'}
report={'checks':checks,'all_pass':all(checks.values()),'base':BASE,'before_terminals':len(a),'after_terminals':len(b),'nets':len(set(b.values())),'expected_changed_terminals':{k:{'before':a.get(k),'after':b.get(k)} for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)},'modified_existing_files':changed,'source_sha256':sha(source.read_bytes()),'timestamp':datetime.datetime.now().astimezone().isoformat()}
(H/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
assert report['all_pass']
