"""Read-only checks on saved KiCad files and exported schematic netlist."""
import json,xml.etree.ElementTree as ET,collections
import pcbnew as p
from design import ROOT
b=p.LoadBoard(str(ROOT/'a2_usb_uart.kicad_pcb'))
tree=ET.parse(ROOT/'reports/schematic.net.xml')
def normalize(name):return name.replace('{slash}','/')
sch={}
for net in tree.findall('.//nets/net'):
    for node in net.findall('node'):
        if not node.attrib['ref'].startswith('#'):
            sch[(node.attrib['ref'],node.attrib['pin'])]=normalize(net.attrib['name'])
pcb={}
for f in b.GetFootprints():
    for pad in f.Pads():
        if pad.GetNumber():pcb[(f.GetReference(),pad.GetNumber())]=normalize(pad.GetNetname())
errors=[{'pin':key,'schematic':sch.get(key),'pcb':pcb.get(key)} for key in sorted(set(sch)|set(pcb)) if sch.get(key)!=pcb.get(key)]
edge_points=[q for g in b.GetDrawings() if g.GetLayer()==p.Edge_Cuts for q in [g.GetStart(),g.GetEnd()]]
board_size=[p.ToMM(max(getattr(q,k) for q in edge_points)-min(getattr(q,k) for q in edge_points)) for k in ['x','y']]
lengths=collections.defaultdict(float);vias=collections.Counter()
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):vias[t.GetNetname()]+=1
    else:lengths[t.GetNetname()]+=p.ToMM(t.GetLength())
result={'board_mm':board_size,
 'thickness_mm':p.ToMM(b.GetDesignSettings().GetBoardThickness()),
 'copper_layers':b.GetCopperLayerCount(),'parts':len(list(b.GetFootprints())),
 'back_parts':[f.GetReference() for f in b.GetFootprints() if f.GetLayer()!=p.F_Cu],
 'terminal_count':len(sch),'terminal_net_mismatches':errors,
 'ground_zones':[p.LayerName(z.GetLayer()) for z in b.Zones() if z.GetNetname()=='/GND'],
 'usb_track_total_mm':{n:round(lengths[n],3) for n in ['/USB_D+','/USB_D-']},
 'usb_vias':{n:vias[n] for n in ['/USB_D+','/USB_D-']},
 'usb_metric_note':'Total copper lengths include ESD branches; not a verified differential path/skew or impedance result',
 'header_nets':{ref:{pad.GetNumber():pad.GetNetname() for pad in f.Pads()} for ref in ['J2','J3'] for f in b.GetFootprints() if f.GetReference()==ref}}
(ROOT/'reports/verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert not errors,errors
assert abs(result['board_mm'][0]-22)<.001 and abs(result['board_mm'][1]-50)<.001
assert result['thickness_mm']==1.6 and result['copper_layers']==2 and not result['back_parts']
assert set(result['header_nets']['J2'].values())=={'/GND','/TXD','/RXD','/USB5V_OUT'}
assert set(result['header_nets']['J3'].values())=={'/RTS_N','/CTS_N','/GND','/VIO_OUT'}
print(json.dumps(result,indent=2))
