from pathlib import Path
import pcbnew as p,json,math,sys,subprocess
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'reports/pcb_review_batch1';CLI=Path.home()/'AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe'
b=p.LoadBoard(str(ROOT/'a2_usb_uart.kicad_pcb'));KEEP=list(b.GetTracks());fps={f.GetReference():f for f in b.GetFootprints()}
def xy(v):return (round(p.ToMM(v.x),6),round(p.ToMM(v.y),6))
def v(x,y):return p.VECTOR2I(p.FromMM(float(x)),p.FromMM(float(y)))
def pad(r,n):return next(a for a in fps[r].Pads() if a.GetNumber()==str(n))
def remove(t):KEEP.append(t);b.Remove(t)
def tr(a,c,net,z=p.F_Cu,w=.18):
 if math.dist(a,c)<1e-7:return
 t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetLayer(z);t.SetWidth(p.FromMM(w));t.SetNet(b.FindNet(net));b.Add(t);KEEP.append(t);return t
def line(points,net,z=p.F_Cu,w=.18):return [tr(a,c,net,z,w) for a,c in zip(points,points[1:])]
def via(x,y,net):
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetViaType(p.VIATYPE_THROUGH);t.SetWidth(p.FromMM(.6));t.SetDrill(p.FromMM(.3));t.SetNet(b.FindNet(net));b.Add(t);KEEP.append(t);return t

def save(fill=False):
 for r in ['SW1','SW2','SW3']:
  name='unconnected-('+r+('-1V8{slash}open-Pad1)' if r=='SW1' else '-OFF{slash}open-Pad1)');net=b.FindNet(name)
  if net is None:net=p.NETINFO_ITEM(b,name);b.Add(net)
  pad(r,1).SetNet(net)
 if fill:p.ZONE_FILLER(b).Fill(b.Zones())
 p.SaveBoard(str(ROOT/'a2_usb_uart.kicad_pcb'),b)
def drc(name,fill=True):
 save(fill);path=OUT/'after'/('drc_'+name+'.json');subprocess.run([str(CLI),'pcb','drc','--format','json','--severity-all','-o',str(path),str(ROOT/'a2_usb_uart.kicad_pcb')],check=True);return json.loads(path.read_text())
