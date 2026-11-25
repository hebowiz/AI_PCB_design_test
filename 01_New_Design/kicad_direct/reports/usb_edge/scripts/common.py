"""PCB quality revision helpers. Operate only on the dedicated worktree copy."""
from pathlib import Path
import pcbnew as k,json,math,subprocess,hashlib,sys,os
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'reports/usb_edge';BOARD=OUT/'candidate/a2_usb_uart.kicad_pcb';CLI=Path.home()/'AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe'
assert 'a2-pcb-quality' in str(ROOT)
if os.environ.get('A2_CANDIDATE_BOARD'):
 BOARD=Path(os.environ['A2_CANDIDATE_BOARD']).resolve();assert str(BOARD).startswith(str(OUT.resolve()))
b=k.LoadBoard(str(BOARD));KEEP=list(b.GetTracks());fps={f.GetReference():f for f in b.GetFootprints()}
xy=lambda q:(round(k.ToMM(q.x),6),round(k.ToMM(q.y),6))
v=lambda x,y:k.VECTOR2I(k.FromMM(float(x)),k.FromMM(float(y)))
uid=lambda t:t.m_Uuid.AsString()
def pad(ref,num):return next(p for p in fps[ref].Pads() if p.GetNumber()==str(num))
def remove(t):KEEP.append(t);b.Remove(t)
def track(a,c,net,layer=k.F_Cu,w=.15):
 if math.dist(a,c)<.000001:return None
 t=k.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(k.FromMM(w));t.SetLayer(layer);t.SetNet(b.FindNet(net));b.Add(t);KEEP.append(t);return t

def via(q,net):
 t=k.PCB_VIA(b);t.SetPosition(v(*q));t.SetLayerPair(k.F_Cu,k.B_Cu);t.SetViaType(k.VIATYPE_THROUGH);t.SetWidth(k.FromMM(.6));t.SetDrill(k.FromMM(.3));t.SetNet(b.FindNet(net));b.Add(t);KEEP.append(t);return t

def count():
 b.BuildConnectivity();b.GetConnectivity().RecalculateRatsnest();return b.GetConnectivity().GetUnconnectedCount(False)
def record(t):return {'uuid':uid(t),'net':t.GetNetname(),'a':xy(t.GetStart()),'b':xy(t.GetEnd()),'layer':t.GetLayer(),'width':k.ToMM(t.GetWidth(k.F_Cu) if isinstance(t,k.PCB_VIA) else t.GetWidth()),'via':isinstance(t,k.PCB_VIA)}
def save(fill=True):
 for r in ['SW1','SW2','SW3']:
  name='unconnected-('+r+('-1V8{slash}open-Pad1)' if r=='SW1' else '-OFF{slash}open-Pad1)');net=b.FindNet(name)
  if net is None:net=k.NETINFO_ITEM(b,name);b.Add(net)
  pad(r,1).SetNet(net)
 if fill:k.ZONE_FILLER(b).Fill(b.Zones())
 k.SaveBoard(str(BOARD),b)
def drc(name):
 save();p=OUT/'checks'/('drc_'+name+'.json');subprocess.run([str(CLI),'pcb','drc','--format','json','--severity-all','-o',str(p),str(BOARD)],check=True);r=json.loads(p.read_text());print('DRC',name,len(r['violations']),len(r['unconnected_items']),flush=True);return r

