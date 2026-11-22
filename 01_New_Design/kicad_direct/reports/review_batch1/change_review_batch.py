"""Targeted R-0002/3/4 edits. Does not run any original generator.
Run once to patch exact e4e46cf baseline; --export-after only reexports/rechecks.
"""
from pathlib import Path
import os,sys,copy,uuid,subprocess,json,hashlib,datetime,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent; R=H.parents[1]; ROOT=R.parents[1]
sys.path.insert(0,str(R/'scripts'));from sexpr import *
BASE='e4e46cf7f6c4286d6ff57e220f6d0643bf028347';REL='01_New_Design/kicad_direct/a2_usb_uart.kicad_sch';source=ROOT/REL
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
 assert source.read_bytes()==base,'Refuse patch: source no longer equals reviewed baseline'
 export('before');s=parse(base.decode('utf-8-sig'));objs={ref(o):o for o in children(s,'symbol')}
 def value(r,n,v):prop(objs[r],n)[2]=Q(v)
 value('Y1','Value','12MHz 12pF');value('Y1','MPN','ABM8-12.000MHZ-12-B1U-T');value('Y1','Datasheet','https://abracon.com/Resonators/abm8.pdf')
 value('Y1','Note','R-0002: +/-10 ppm initial, +/-10 ppm temperature (-20..70 C), +/-2 ppm first year. 15pF loads assume 4.5pF stray; verify frequency/start-up/drive on PCB.')
 for r in ('C13','C14'):
  value(r,'Value','15p 1%');value(r,'MPN','GRM1555C1H150FA01D');value(r,'Datasheet','https://www.icbanq.com/icdownload/V2_DATA/ICBShop/Board/Murata/GRM1555C1H150FA01-01.pdf');value(r,'Note','R-0002: C0G 50V 1%; CL = 15/2 + 4.5 pF assumed stray = 12 pF. Tune after measurement.')
 value('U1','Note','R-0004: USB5V into VREGIN; VCCD supplies +3V3. UART/LED/PWREN EEPROM programming required.')
 value('C1','Note','R-0004: USB5V input bulk retained; place at U1 VREGIN on future PCB update.')
 value('C2','Note','R-0004: +3V3 VCCD output bulk retained; verify effective capacitance and place at U1 on future PCB update.')
 s.remove(objs['U3']);s.remove(objs['#PWR0136'])
 # Remove only wires/markers belonging to the removed regulator, plus the VREGIN/VCCD tie.
 edges=[((52,185),(54,185)),((54,185),(54,187)),((54,185),(59,185)),((54,187),(59,187)),((65,193),(65,195)),((71,185),(79,185)),((143,101),(151,101)),((151,99),(151,101))]
 for a,b in edges:
  matches=[w for w in children(s,'wire') if {tuple(map(float,p[1:])) for p in one(w,'pts')[1:]}=={tuple(pt(*a)),tuple(pt(*b))}]
  assert len(matches)==1,(a,b);s.remove(matches[0])
 for typ,coords in [('junction',[(54,185),(52,185),(79,185),(151,101)]),('no_connect',[(69,187)])]:
  for xy in coords:
   m=[o for o in children(s,typ) if tuple(map(float,one(o,'at')[1:3]))==tuple(pt(*xy))];assert len(m)==1,(typ,xy);s.remove(m[0])
 def label(name,x,y,angle=0,size=0.7):s.append(['global_label',Q(name),['shape','output' if name=='+3V3' else 'input'],['at',*pt(x,y),angle],['effects',['font',['size',size,size]],['justify','right']],['uuid',uid()]])
 # Existing 2.54mm stubs end at these labels; no direct label-on-pin attachment.
 label('+3V3',151,99);label('USB5V',151,101)
 # Preserve library definitions: explicit PWR_FLAG declares VCCD output in this 5V mode.
 f=copy.deepcopy(objs['#FLG01']);new='#FLG'+str(max(int(r[4:]) for r in objs if r.startswith('#FLG'))+1).zfill(2);assert new not in objs
 dx,dy=pt(88,185);ox,oy=map(float,one(f,'at')[1:3]);one(f,'at')[1:3]=[dx,dy];one(f,'uuid')[1]=uid();prop(f,'Reference')[2]=Q(new)
 prop(f,'Note')[2]=Q('R-0004: VCCD is 3.3V source with VREGIN=5V; generic U1 library retains power_in pin type.')
 for p in children(f,'property'):
  at=one(p,'at');at[1]=round(float(at[1])+dx-ox,5);at[2]=round(float(at[2])+dy-oy,5)
 for p in children(f,'pin'):one(p,'uuid')[1]=uid()
 for pr in children(one(f,'instances'),'project'):
  for pa in children(pr,'path'):one(pa,'reference')[1]=Q(new)
 s.append(f)
 replacements={
 'D2: USB power':'D2: I ~ 0.30 mA = (5V - 2.0V) / 10k',
 'D3/D4: U1 active-low sinks':'D3/D4: I(on) ~ 0.28 mA each = (3.3V - 2.0V) / 4.7k',
 '04  POWER TREE: THREE BRANCHES FROM USB5V':'04  POWER: U1 INTERNAL 3V3 / U4 VIO / U6 SWITCHED 5V',
 'U3: fixed +3V3 -> U1 / U2 VCCA / EEPROM / control':'U3 removed. USB5V -> U1.40 VREGIN (see block 01).',
 'EN tied to input. VPHY / VPLL are filtered +3V3 branches.':'U1.39 VCCD -> +3V3 -> U1 / U2 VCCA / EEPROM / control.',
 'USB5V -> U3 -> +3V3 -> FB1 / FB2 -> VPHY / VPLL':'USB5V -> U1 internal regulator -> +3V3 -> FB1 / FB2',
 'R-0001: D1/D5 ESD321DPYR; PCB/BOM not updated.':'R-0001 retained; R-0002/3/4 revised. PCB/BOM not updated.',
 'R-0001 schematic. Human review pending; not approved.':'R-0002/3/4: human review pending. Not for fabrication.'}
 for t in children(s,'text'):
  if str(t[1]) in replacements:t[1]=Q(replacements[str(t[1])])
 def text(msg,x,y,size=1.05):s.append(['text',Q(msg),['at',*pt(x,y),0],['effects',['font',['size',size,size]],['justify','left','bottom']],['uuid',uid()]])
 text('Estimates: Vf=2.0V; TX/RX VOL=0V. Verify actual brightness.',396,108)
 text('TX/RX average current depends on activity / pulse timing.',396,114)
 text('Y1: +/-10 ppm initial / +/-10 ppm temp (-20..70C).',85,136)
 text('CL = 15pF / 2 + 4.5pF assumed stray = 12pF.',85,142)
 text('Verify total frequency error, start-up and crystal drive on PCB.',85,148)
 text('USB5V bulk',43,200);text('VCCD bulk (U1.39 output)',78,200)
 text('3V3 flag declares U1.39 output with VREGIN=5V.',111,205)
 text('C1/C2 retained: place near U1 in PCB update.',111,211)
 one(one(s,'title_block'),'rev')[1]=Q('A2-R0002-4 REVIEW')
 source.write_text(dump(s)+'\n',encoding='utf8')
export('after')
from PIL import Image,ImageDraw
boxes={'clock':(85,25,150,65),'power_pins':(115,87,177,120),'power_tree':(16,174,220,217),'leds':(389,30,463,119),'usb':(16,25,82,65),'clock_notes':(79,132,189,154)}
for v in ('before','after'):
 im=Image.open(H/v/'schematic.png').convert('RGB');f=im.width/(594/1.27)
 for n,b in boxes.items():im.crop(tuple(round(c*f) for c in b)).save(H/v/(n+'.png'))
 im.resize((1680,1188)).save(H/v/'overview.png')
for n in boxes:
 pics=[Image.open(H/v/(n+'.png')) for v in ('before','after')];c=Image.new('RGB',(sum(p.width for p in pics),max(p.height for p in pics)+30),'white');d=ImageDraw.Draw(c);x=0
 for title,p in zip(('Before (R-0001 applied)','After (R-0002/3/4)'),pics):c.paste(p,(x,30));d.text((x+10,10),title,fill='black');x+=p.width
 c.save(H/('comparison_'+n+'.png'))
def pins(p):return {n.get('ref')+'.'+n.get('pin'):net.get('name') for net in ET.parse(p).findall('.//nets/net') for n in net.findall('node')}
def comps(p):return {e.get('ref'):e for e in ET.parse(p).findall('.//components/comp')}
a=pins(H/'before/netlist.xml');b=pins(H/'after/netlist.xml');expected={k:v for k,v in a.items() if not k.startswith('U3.')};expected['U1.40']='USB5V'
ca=comps(H/'before/netlist.xml');cb=comps(H/'after/netlist.xml');sa=parse(base.decode('utf-8-sig'));sb=parse(source.read_text());oa={ref(o):o for o in children(sa,'symbol')};ob={ref(o):o for o in children(sb,'symbol')}
attr_allowed={'Y1':{'MPN','Value','Note','Datasheet'},'C13':{'MPN','Value','Note','Datasheet'},'C14':{'MPN','Value','Note','Datasheet'},'U1':{'Note'},'C1':{'Note'},'C2':{'Note'}}
props=lambda o:{str(p[1]):str(p[2]) for p in children(o,'property')}
attr_delta={r:{k:{'before':props(oa[r])[k],'after':props(ob[r])[k]} for k in props(oa[r]) if props(oa[r])[k]!=props(ob[r])[k]} for r in cb}
attr_delta={r:v for r,v in attr_delta.items() if v}
checks={'terminal_nets_exact_expected_delta':expected==b,'only_U3_removed':set(ca)-set(cb)=={'U3'} and not(set(cb)-set(ca)),'attributes_only_approved':all(set(v)<=attr_allowed.get(r,set()) for r,v in attr_delta.items()),'all_library_definitions_unchanged':one(sa,'lib_symbols')==one(sb,'lib_symbols'),'all_retained_real_symbol_UUIDs_preserved':all(one(oa[r],'uuid')==one(ob[r],'uuid') for r in cb),'R1_R5_R6_symbols_unchanged':all(oa[r]==ob[r] for r in ['D1','D5','U6','Q1','R5','R6','R16','SW2','U5','R3','R4']),'no_5V_on_VCCD':b['U1.39']=='+3V3' and b['U1.40']=='USB5V','all_retained_footprints_equal':all(props(oa[r])['Footprint']==props(ob[r])['Footprint'] for r in cb)}
for v in ('before','after'):
 er=json.loads((H/v/'erc.json').read_text());checks[v+'_ERC_zero_violations']=not[i for sh in er['sheets'] for i in sh['violations']]
checks['ERC_settings_unchanged']=json.loads((H/'before/erc.json').read_text())['ignored_checks']==json.loads((H/'after/erc.json').read_text())['ignored_checks']
changed=git('diff','--name-only',BASE).decode().splitlines();checks['only_existing_schematic_changed']=changed==[REL]
protected={}
for path in git('ls-tree','-r','--name-only',BASE,'01_New_Design/kicad_direct').decode().splitlines():
 if path==REL:continue
 current=ROOT/path
 protected[path]=git('hash-object','--path='+path,str(current)).strip()==git('rev-parse',BASE+':'+path).strip()
checks['all_other_existing_A2_files_unchanged']=all(protected.values())
result=dict(checks=checks,all_pass=all(checks.values()),base=BASE,timestamp=datetime.datetime.now().astimezone().isoformat(),before_components=len(ca),after_components=len(cb),before_terminals=len(a),after_terminals=len(b),before_nets=len(set(a.values())),after_nets=len(set(b.values())),terminal_delta={k:{'before':a.get(k),'after':b.get(k)} for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)},attribute_delta=attr_delta,modified_existing_files=changed,source_sha256=sha(source.read_bytes()))
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');(H/'preservation.json').write_text(json.dumps(protected,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2));assert result['all_pass']

