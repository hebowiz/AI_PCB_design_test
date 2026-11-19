"""Synchronize schematic metadata and no-connect nets without replacing routes."""
import json,csv,xml.etree.ElementTree as ET
import pcbnew as p
from design import ROOT,PARTS
b=p.LoadBoard(str(ROOT/'a2_usb_uart.kicad_pcb'))
b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
parts={i['ref']:i for i in PARTS}
footprints={f.GetReference():f for f in b.GetFootprints()}
for ref,f in footprints.items():
    for key in ['MPN','Note']:
        f.SetField(key,parts[ref][key.lower()])
        f.GetField(key).SetVisible(False)
netlist=ET.parse(ROOT/'reports/schematic.net.xml')
for n in netlist.findall('.//nets/net'):
    name=n.attrib['name']
    if not name.startswith('unconnected-'):continue
    name=name.replace('/', '{slash}')
    net=b.FindNet(name)
    if net is None:net=p.NETINFO_ITEM(b,name);b.Add(net)
    for pin in n.findall('node'):
        f=footprints[pin.attrib['ref']]
        for pad in f.Pads():
            if pad.GetNumber()==pin.attrib['pin']:pad.SetNet(net)
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(ROOT/'a2_usb_uart.kicad_pcb'),b)
(ROOT/'reports/design_manifest.json').write_text(json.dumps(PARTS,indent=2),encoding='utf-8')
with (ROOT/'reports/bom.csv').open('w',newline='',encoding='utf-8-sig') as fh:
    w=csv.writer(fh);w.writerow(['Reference','Value','MPN','Footprint','Notes'])
    for a in PARTS:w.writerow([a[k] for k in ['ref','value','mpn','footprint','note']])
print('Updated 1.6 mm thickness, metadata, no-connect nets, ground fills and BOM')
