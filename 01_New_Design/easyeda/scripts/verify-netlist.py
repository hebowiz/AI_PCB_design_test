"""Compare EasyEDA Pro's exported netlist with the intended pin/net mapping."""
import json, re, sys
from pathlib import Path
b=Path(__file__).resolve().parents[1]
expected=json.loads((b/'reports/schematic-final-connections.json').read_text(encoding='utf-8-sig'))['value']['expected']
source_path=Path(sys.argv[1]) if len(sys.argv)>1 else b/'reports/A3-netlist.net'
source=source_path.read_text(encoding='utf-8-sig')
actual={}
for block in re.findall(r'^\(\s*\n(.*?)^\)\s*$',source,re.M|re.S):
    lines=block.strip().splitlines(); net=lines[0].strip()
    for line in lines[1:]:
        pin=line.split()[0]
        if pin in actual and actual[pin]!=net: raise ValueError('Duplicate pin '+pin)
        actual[pin]=net
errors=[]
for ref,pins in expected.items():
    for pin,net in pins.items():
        key=f'{ref}-{pin}'; found=actual.get(key)
        if net is None:
            if found and not found.startswith('$'): errors.append([key,None,found])
        elif found!=net: errors.append([key,net,found])
unknown=sorted(set(actual)-{f'{ref}-{p}' for ref,ps in expected.items() for p in ps})
result={'passed':not errors and not unknown,'expectedComponents':len(expected),'expectedConnectedPins':sum(n is not None for p in expected.values() for n in p.values()),'actualPins':len(actual),'mismatches':errors,'unknownPins':unknown}
output=Path(sys.argv[2]) if len(sys.argv)>2 else b/'reports/netlist-verification.json'
output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
