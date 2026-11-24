from common import *
old=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));present={uid(t) for t in b.GetTracks()};restored=[]
for t in old.GetTracks():
 if t.GetNetname() in ['/USB_D+','/USB_D-'] and uid(t) not in present:
  assert not isinstance(t,k.PCB_VIA)
  nt=track(xy(t.GetStart()),xy(t.GetEnd()),t.GetNetname(),t.GetLayer(),k.ToMM(t.GetWidth()));nt.SetUuid(k.KIID(uid(t)));restored.append(record(nt))
(OUT/'restored_protected_usb.json').write_text(json.dumps(restored,indent=2))
fps['D1'].Reference().SetPosition(v(110.55,107.8));fps['D5'].Reference().SetPosition(v(109.3,107.8));fps['C14'].Reference().SetPosition(v(112.1,107.9))
drc('protected_usb_restored')
