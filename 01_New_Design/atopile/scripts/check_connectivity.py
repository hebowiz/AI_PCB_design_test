"""Compare exported schematic and PCB connectivity against the authored manifest."""
import collections
import csv
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'board/design.json').read_text(encoding='utf-8'))
expected={};nc=set()
for c in data['components']:
    for pin,net in c['nets'].items():
        key=(c['ref'],pin)
        if net:expected[key]=net
        else:nc.add(key)
b=k.LoadBoard(str(ROOT/'board/a1.kicad_pcb'));actual={};bynet=collections.defaultdict(set)
for f in b.GetFootprints():
    for p in f.Pads():
        key=(f.GetReference(),p.GetNumber())
        if p.GetNumber():
            actual[key]=p.GetNetname();bynet[p.GetNetname()].add(key)
sch={};schnc=set()
xml=ET.parse(ROOT/'reports/schematic.net.xml')
for net in xml.findall('./nets/net'):
    name=net.attrib['name'].lstrip('/')
    for node in net.findall('node'):
        if node.attrib['ref'].startswith('#'):continue
        key=(node.attrib['ref'],node.attrib['pin'])
        if name.startswith('unconnected-'):schnc.add(key)
        else:sch[key]=name
errors=[]
for key,net in expected.items():
    if actual.get(key)!=net:errors.append(f'PCB {key}: {actual.get(key)} != {net}')
    if sch.get(key)!=net:errors.append(f'SCH {key}: {sch.get(key)} != {net}')
for key in nc:
    if key not in actual:errors.append(f'Missing NC PCB {key}')
    elif len(bynet[actual[key]])!=1:errors.append(f'NC pin joins other pins: {key}: {bynet[actual[key]]}')
    if key not in schnc:errors.append(f'Missing schematic no-connect {key}')
for key in set(actual)-set(expected)-nc:errors.append(f'Undeclared PCB pad {key}')
for key in set(sch)-set(expected):errors.append(f'Undeclared schematic pin {key}')
report=dict(errors=errors,named_nets=len(set(expected.values())),connected_pin_assignments=len(expected),
    intentional_unconnected_pins=len(nc),pcb_unique_numbered_pads=len(actual),
    schematic_connected_pin_assignments=len(sch),scope='Compare authored pin manifest, KiCad schematic export and actual PCB pads; duplicate shell pad numbers collapsed.')
(ROOT/'reports/connectivity.json').write_text(json.dumps(report,indent=2)+'\n')
with (ROOT/'reports/pin_net.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['Reference','Pin','Authored net','PCB net','Schematic net'])
    for key in sorted(set(expected)|nc):w.writerow([*key,expected.get(key,'NC'),actual.get(key),sch.get(key,'NC')])
print(json.dumps(report,indent=2));sys.stdout.flush();os._exit(bool(errors))
