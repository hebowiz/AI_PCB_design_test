from pathlib import Path
import pcbnew as p,json,tempfile,subprocess,math
OUT=Path(__file__).resolve().parent;tmp=Path(tempfile.mkdtemp(prefix='a2-rule-boundary-'));b=p.BOARD();nets=[]
for name in ['TEST_A','TEST_B']:
 n=p.NETINFO_ITEM(b,name);b.Add(n);nets.append(n)
def pt(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def via(x,y,net):
 v=p.PCB_VIA(b);v.SetPosition(pt(x,y));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(nets[net]);b.Add(v);return v
cases=[]
for k,(gap,same) in enumerate([(0,True),(.199,True),(.201,True),(.15,False)]):
 x=10+k*8;f=p.FOOTPRINT(b);f.SetReference('PAD'+str(k));f.SetPosition(pt(x,10));b.Add(f);a=p.PAD(f);a.SetNumber('1');a.SetAttribute(p.PAD_ATTRIB_SMD);a.SetShape(p.PAD_SHAPE_RECT);a.SetSize(pt(1,1));layers=p.LSET();layers.AddLayer(p.F_Cu);a.SetLayerSet(layers);a.SetPosition(pt(x,10));a.SetNet(nets[0]);f.Add(a);v=via(x+.5+.25+gap,10,0 if same else 1);cases.append({'id':'pad_via_'+str(k),'pair':[a.m_Uuid.AsString(),v.m_Uuid.AsString()],'gap':gap,'same_net':same,'expected_violation':same and gap<.2,'rule':'R0019'})
for k,(gap,same) in enumerate([(0,True),(.499,True),(.501,True),(.3,False)]):
 x=10+k*8;a=via(x,20,0);v=via(x+.5+gap,20,0 if same else 1);cases.append({'id':'via_via_'+str(k),'pair':[a.m_Uuid.AsString(),v.m_Uuid.AsString()],'gap':gap,'same_net':same,'expected_violation':same and gap<.5,'rule':'R0020'})
p.SaveBoard(str(tmp/'fixture.kicad_pcb'),b);(tmp/'fixture.kicad_dru').write_bytes((OUT/'proposed_rules.txt').read_bytes())
cli=Path.home()/'AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe';r=subprocess.run([str(cli),'pcb','drc','--format','json','--severity-all','-o',str(OUT/'rule_boundary_drc.json'),str(tmp/'fixture.kicad_pcb')],capture_output=True,text=True);assert r.returncode==0,r.stderr
d=json.loads((OUT/'rule_boundary_drc.json').read_text())
for c in cases:
 c['actual_violation']=any(c['rule'] in v.get('description','') and {x['uuid'] for x in v['items']}==set(c['pair']) for v in d['violations'])
 c['pass']=c['actual_violation']==c['expected_violation']
assert all(c['pass'] for c in cases),cases
(OUT/'rule_boundary_results.json').write_text(json.dumps(cases,indent=2));print(json.dumps(cases,indent=2))
