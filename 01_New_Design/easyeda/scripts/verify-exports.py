"""Check local exports without sending files to a manufacturing service."""
import csv,json,zipfile
from pathlib import Path
b=Path(__file__).resolve().parents[1]
def read_table(p):
    raw=p.read_bytes();encoding='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'
    return list(csv.DictReader(raw.decode(encoding).splitlines(),delimiter='\t')),encoding
bom,be=read_table(b/'exports/A3-USB-UART-BOM.csv');pn,pe=read_table(b/'exports/A3-USB-UART-PickPlace.csv')
with zipfile.ZipFile(b/'exports/A3-USB-UART-Gerber.zip') as z:
    r={'bomLines':len(bom),'bomQuantity':sum(int(x['Quantity']) for x in bom),'pickPlaceCount':len(pn),'allTop':all(x['Layer']=='T' for x in pn),'uniqueDesignators':len({x['Designator'] for x in pn}),'zipCrcError':z.testzip(),'requiredLayersPresent':all(n in z.namelist() for n in ['Gerber_TopLayer.GTL','Gerber_BottomLayer.GBL','Gerber_BoardOutlineLayer.GKO','Drill_PTH_Through.DRL','Drill_PTH_Through_Via.DRL']),'bomEncoding':be,'pickPlaceEncoding':pe,'delimiter':'tab','viaDrillHeader':z.read('Drill_PTH_Through_Via.DRL').decode('utf-8').split('%')[0]}
r['passed']=r['bomQuantity']==53 and r['pickPlaceCount']==53 and r['allTop'] and r['uniqueDesignators']==53 and r['zipCrcError'] is None and r['requiredLayersPresent']
(b/'reports/manufacturing-validation.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 1)
