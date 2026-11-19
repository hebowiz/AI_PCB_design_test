"""KiCad 10 placement and fixed copper for the A-1 generated layout.
Only run on this task's generated PCB; prep replaces board/a1.kicad_pcb.
"""
import json
import math
import os
from pathlib import Path
import sys
import uuid
import pcbnew as k

ROOT=Path(__file__).resolve().parents[1]
BOARD=ROOT/'board'
REPORTS=ROOT/'reports'
mm=k.FromMM
vec=lambda x,y:k.VECTOR2I(mm(x),mm(y))
data=json.loads((BOARD/'design.json').read_text(encoding='utf-8'))
items={c['ref']:c for c in data['components']}


def project():
    classes=[dict(name='Default',clearance=.15,track_width=.15,via_diameter=.5,via_drill=.25,
        uvia_diameter=.3,uvia_drill=.1,diff_pair_width=.25,diff_pair_gap=.15,diff_pair_via_gap=.25)]
    classes += [dict(classes[0],name='Power',track_width=.25,priority=1),
                dict(classes[0],name='USB',track_width=.25,priority=0)]
    pro=dict(meta=dict(filename='a1.kicad_pro',version=1),
        board=dict(design_settings=dict(rules=dict(min_clearance=.15,min_track_width=.15,
            min_via_diameter=.5,min_through_hole_diameter=.25,min_hole_clearance=.25,
            min_copper_edge_clearance=.3),
            rule_severities=dict(courtyards_overlap='error',unconnected_items='error'))),
        net_settings=dict(classes=classes,netclass_patterns=[
            *[dict(netclass='Power',pattern=n) for n in ['VBUS*','VIO*','USB5V_OUT']],
            dict(netclass='USB',pattern='USB_D*')]))
    (BOARD/'a1.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
    (BOARD/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "parts") (type "KiCad") (uri "${KIPRJMOD}/parts") (options "") (descr "Local A-1 library")))\n')


def inventory(b):
    pads={}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            pads[(fp.GetReference(),p.GetNumber())]=dict(x=k.ToMM(p.GetPosition().x),
                y=k.ToMM(p.GetPosition().y),net=p.GetNetname(),code=p.GetNetCode())
    return pads


def track(b,net,points,width=.18,layer=k.F_Cu,locked=True):
    code=b.FindNet(net).GetNetCode()
    for a,z in zip(points,points[1:]):
        if a==z: continue
        t=k.PCB_TRACK(b); t.SetStart(vec(*a)); t.SetEnd(vec(*z))
        t.SetWidth(mm(width)); t.SetLayer(layer); t.SetNetCode(code); t.SetLocked(locked); b.Add(t)


def via(b,net,x,y,locked=True):
    v=k.PCB_VIA(b); v.SetPosition(vec(x,y)); v.SetWidth(mm(.6)); v.SetDrill(mm(.3))
    v.SetViaType(k.VIATYPE_THROUGH); v.SetLayerPair(k.F_Cu,k.B_Cu)
    v.SetNetCode(b.FindNet(net).GetNetCode()); v.SetLocked(locked); b.Add(v)


def prep():
    project()
    b=k.LoadBoard(str(BOARD/'layouts/default/default.kicad_pcb'))
    # Cached values and lists before destructive operations.
    fps=list(b.GetFootprints()); drawings=list(b.GetDrawings()); zones=list(b.Zones()); tracks=list(b.GetTracks())
    for obj in drawings+zones+tracks: b.Remove(obj)
    b.SetCopperLayerCount(2); b.GetDesignSettings().SetBoardThickness(mm(1.6))
    for fp in fps:
        ref=fp.GetReference(); comp=items[ref]; x,y,angle=comp['position']
        fp.SetOrientationDegrees(angle); fp.SetPosition(vec(x,y)); fp.SetValue(comp['value'])
        fp.SetField('MPN',comp['mpn']); fp.SetField('Manufacturer',comp['manufacturer'])
        fp.SetField('atopile_address',comp['name'])


        text=fp.Reference(); text.SetTextSize(vec(.7,.7)); text.SetTextThickness(mm(.1))
        text.SetTextAngleDegrees(0); text.SetPosition(vec(x,y-1.8)); text.SetVisible(True)
        fp.Value().SetVisible(False)
        for field in fp.GetFields():
            if field.GetName() not in ('Reference','Value'): field.SetVisible(False)
    for a,z in zip([(0,0),(22,0),(22,50),(0,50)],[(22,0),(22,50),(0,50),(0,0)]):
        line=k.PCB_SHAPE(b); line.SetShape(k.SHAPE_T_SEGMENT);line.SetLayer(k.Edge_Cuts)
        line.SetStart(vec(*a));line.SetEnd(vec(*z));line.SetWidth(mm(.05));b.Add(line)
    pads=inventory(b)
    def xy(ref,pin):
        p=pads[(ref,str(pin))];return(p['x'],p['y'])
    # USB crossover is explicit, locked, and reviewed as a high-speed limitation.
    # Width is provisional until the 1.6 mm fabricator stackup is agreed.
    # Local crossover uses two DM vias; impedance/return continuity needs review.
    dm=xy('U1',6);dp=xy('U1',7)
    track(b,'USB_DM',[xy('J1',2),(10,6.9)],.25)
    track(b,'USB_DP',[xy('J1',3),(12,6.9)],.25)
    # ESD pads attach as a short branch to the adjacent USB run.
    for ref,net,x in [('D4','USB_DM',10),('D5','USB_DP',12)]:
        p=xy(ref,1);track(b,net,[p,(x,p[1])],.25)
    via(b,'USB_DM',10,7.1);via(b,'USB_DM',11.75,8.65)
    track(b,'USB_DM',[(10,6.9),(10,7.1)],.25)
    track(b,'USB_DM',[(10,7.1),(10.2,7.1),(11.75,8.65)],.25,k.B_Cu)
    track(b,'USB_DM',[(11.75,8.65),(11.25,8.65),dm],.25)
    track(b,'USB_DP',[(12,6.9),(12,7.2),(10.75,8.4),dp],.25)
    # Local regulator feedback remains short and independent of export switch.
    # Fixed net paths are kept in this script for repeatable iteration.
    k.SaveBoard(str(BOARD/'a1.kicad_pcb'),b)
    project() # SaveBoard copies source project defaults; apply A-1 rules last.
    (REPORTS/'placement.json').write_text(json.dumps({r:c['position'] for r,c in items.items()},indent=2))
    print('Placed',len(fps),'components; generated fixed USB/crystal tracks.')


def post():
    b=k.LoadBoard(str(BOARD/'a1.kicad_pcb'))
    for old in list(b.Zones()): b.Remove(old)
    # Add ground planes only after routing.
    for layer in [k.F_Cu,k.B_Cu]:
        z=k.ZONE(b);z.SetLayer(layer);z.SetNetCode(b.FindNet('GND').GetNetCode())
        z.SetZoneName('A1_GND_'+str(layer));z.SetLocalClearance(mm(.15));z.SetMinThickness(mm(.15))
        z.SetThermalReliefGap(mm(.2));z.SetThermalReliefSpokeWidth(mm(.2))
        z.SetIslandRemovalMode(k.ISLAND_REMOVAL_MODE_ALWAYS)
        outline=z.Outline();outline.NewOutline()
        for x,y in [(.3,.3),(21.7,.3),(21.7,49.7),(.3,49.7)]:outline.Append(mm(x),mm(y))
        b.Add(z)
    k.ZONE_FILLER(b).Fill(b.Zones())
    k.SaveBoard(str(BOARD/'a1.kicad_pcb'),b)
    print('Filled ground zones on both copper layers.')


def verify():
    b=k.LoadBoard(str(BOARD/'a1.kicad_pcb'));pads=inventory(b);errors=[];singletons=[]
    actual_refs={fp.GetReference() for fp in b.GetFootprints()}
    if actual_refs!=set(items):errors.append('Component set mismatch')
    for ref,c in items.items():
        for pin,net in c['nets'].items():
            got=pads.get((ref,pin))
            if got is None:errors.append(f'{ref}.{pin}: missing pad')
            elif net and got['net']!=net:errors.append(f'{ref}.{pin}: expected {net}, got {got["net"]}')
            elif not net:singletons.append(dict(ref=ref,pin=pin,actual_net=got['net']))
    bottom=[fp.GetReference() for fp in b.GetFootprints() if fp.GetLayer()!=k.F_Cu]
    if bottom:errors.append('Unexpected bottom components: '+str(bottom))
    lengths={n:sum(k.ToMM(t.GetLength()) for t in b.GetTracks() if t.GetNetname()==n and not isinstance(t,k.PCB_VIA)) for n in ['USB_DM','USB_DP']}
    vias={n:sum(isinstance(t,k.PCB_VIA) and t.GetNetname()==n for t in b.GetTracks()) for n in lengths}
    fixed=[]
    for t in b.GetTracks():
        if t.IsLocked():
            fixed.append(dict(net=t.GetNetname(),layer=t.GetLayer(),
                start=[t.GetStart().x,t.GetStart().y],end=[t.GetEnd().x,t.GetEnd().y],width=t.GetWidth(k.F_Cu) if isinstance(t,k.PCB_VIA) else t.GetWidth()))
    report=dict(errors=errors,components=len(actual_refs),pads=len(pads),
        unused_pins=singletons,all_front=not bottom,copper_layers=b.GetCopperLayerCount(),
        thickness_mm=k.ToMM(b.GetDesignSettings().GetBoardThickness()),
        usb_length_mm=lengths,usb_vias=vias,usb_skew_mm=abs(lengths['USB_DM']-lengths['USB_DP']),
        fixed_copper=fixed,tracks_and_vias=len(b.GetTracks()))
    (REPORTS/'netlist_check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['unused_pins','fixed_copper']},indent=2))
    return bool(errors)


if __name__=='__main__':
    mode=sys.argv[1];code=0
    if mode=='prep':prep()
    elif mode=='post':post()
    elif mode=='verify':code=verify()
    else:raise ValueError(mode)
    sys.stdout.flush();os._exit(code)
