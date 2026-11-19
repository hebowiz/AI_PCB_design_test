"""Record final artifact hashes and verify BOM/position/output consistency."""
import csv,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
data=read('board/design.json'); refs={c['ref'] for c in data['components']}
drc=read('reports/drc.json');erc=read('reports/erc.json');errors=[]
if drc['violations'] or drc['unconnected_items']:errors.append('PCB DRC not clean')
if any(s['violations'] for s in erc['sheets']):errors.append('Schematic ERC not clean')
if read('reports/connectivity.json')['errors']:errors.append('Connectivity mismatch')
with (ROOT/'manufacturing/review-only/bom.csv').open(encoding='utf-8-sig',newline='') as f:
    bom=list(csv.DictReader(f))
with (ROOT/'manufacturing/review-only/placement.csv').open(encoding='utf-8-sig',newline='') as f:
    positions=list(csv.DictReader(f))
if {r['Reference'] for r in bom}!=refs:errors.append('BOM component mismatch')
if {r['Ref'] for r in positions}!=refs:errors.append('Placement component mismatch')
with zipfile.ZipFile(ROOT/'manufacturing/A1-REVIEW-ONLY.zip') as z:
    if z.testzip():errors.append('ZIP CRC failure')
    for entry in z.infolist():
        p=ROOT/'manufacturing/review-only'/entry.filename
        if z.read(entry)!=p.read_bytes():errors.append('ZIP content mismatch: '+entry.filename)
for line in (ROOT/'manufacturing/SHA256SUMS.txt').read_text(encoding='utf-8-sig').splitlines():
    digest,name=line.split('  ',1)
    if hashlib.sha256((ROOT/'manufacturing/review-only'/name).read_bytes()).hexdigest()!=digest:errors.append('Hash mismatch: '+name)
files=['board/a1.kicad_pcb','board/a1.kicad_pro','board/a1.kicad_sch','board/main.ato',
       'board/design.json','reports/erc.json','reports/drc.json','reports/connectivity.json','manufacturing/A1-REVIEW-ONLY.zip']
report=dict(errors=errors,bom_rows=len(bom),position_rows=len(positions),
    release_status='ENGINEERING_REVIEW_ONLY: SI, crystal routing, via-in-pad, mechanics and hardware tests outstanding',
    sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'reports/artifact_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
