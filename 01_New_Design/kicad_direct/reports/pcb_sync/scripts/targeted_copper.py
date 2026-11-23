"""Explicitly reviewed copper edits; no DRC-category-based deletion."""
from pathlib import Path
import pcbnew as p,json,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'reports/pcb_sync';path=ROOT/'a2_usb_uart.kicad_pcb'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='50af89b0e52bc5fbbdf9ff793f993b31820901ddb370aa8f943a8e053f3ad213','PCB has changed: inspect again'
b=p.LoadBoard(str(path));tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
# Each entry was inspected with both endpoints and the colliding changed pad.
selected={
'4a43f074-abb6-4766-bbce-8c0f4c8f22de':('VPHY','C12.2'),
'dbf0c3fa-ced5-45cd-917b-3904234590d7':('VPHY','C12.2'),
'4e23bf4d-eb27-4e36-a046-5c8fbc046534':('VPHY','C12.2'),
'506de76f-9723-4bf4-862c-b3c5d39d9d07':('VPHY','C12.2'),
'3355d0ea-09db-4c14-be8e-227b965efa24':('VPHY','C12.2'),
'08da1c05-c906-4a30-9890-10bb2fc26917':('/USB_D-','D1.1'),
'ef52759a-2ce5-49a4-8106-fbfb2c2ca91f':('/USB_D-','D1.1'),
'ab2e818c-5688-4945-9f17-d5134fc48927':('/USB_D-','D1.1'),
'826442d1-1396-4509-b3c9-dfd612c1431f':('/USB_D-','D1.1'),
'a8cd6edc-32ef-416b-be3b-1688b8b042cd':('/USB_D+','D1.2'),
'684178d8-98b1-4e1d-9edf-85cea5ebd509':('/USB_D+','D1.2'),
'2ecbc4f3-d496-4319-8028-4dd68bd8a510':('/USB_D+','D1.2'),
'478c1306-acb3-4d0b-bdf0-2b51a1bd1382':('/USB_D+','D1.2'),
'fe08ff8c-8e07-417d-ac1d-4b13e66330c0':('+3V3','C1.1'),
'cc979d03-245a-4323-ad27-402b072e94b4':('+3V3','U1.40'),
'a2bfb54d-3305-4645-9bd0-c1c1f8e590df':('+3V3','C23.2'),
'fc4e1462-61f8-4678-9661-d3ae86795d9e':('/PWR_EN','TP2.1'),
'88c95bec-e605-4fd5-ab22-c534ace1918e':('USB5V','R17.2'),
'1290a95b-287d-48a2-87dd-8bc77db91797':('USB5V','R17.2')}
log=[]
for uid,(net,pad) in selected.items():
 t=tracks[uid];assert t.GetNetname()==net and not isinstance(t,p.PCB_VIA)
 log.append({'uuid':uid,'net':net,'changed_pad':pad,'start':[p.ToMM(t.GetStart().x),p.ToMM(t.GetStart().y)],'end':[p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y)]})
for uid in selected:b.Remove(tracks[uid])
(OUT/'before/placed_before_copper.kicad_pcb').write_bytes(path.read_bytes())
p.SaveBoard(str(path),b)
(OUT/'targeted_copper_edits.json').write_text(json.dumps(log,indent=2),encoding='utf8')
print('Applied 19 inspected local segment removals; preserved all other copper')
