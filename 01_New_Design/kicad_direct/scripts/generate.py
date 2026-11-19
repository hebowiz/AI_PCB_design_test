"""Generate native editable KiCad schematic and placed PCB from A-2 data.

Refuses to replace outputs unless --replace-generated is supplied. Once a human
edits CAD, apply local edits instead of running this generator again.
"""
import argparse, copy, csv, json, math, re, shutil, uuid
from pathlib import Path
import pcbnew as pcb
from sexpr import parse,dump,children,one,Q
from design import ROOT,KICAD,PARTS,FLAGS

NS=uuid.UUID('ce0d53ed-790e-4964-bf06-e2c942c20c53')
def uid(s):return str(uuid.uuid5(NS,s))
SCH_ID=uid('root')
def effects(size=1):return ['effects',['font',['size',size,size]]]
def custom(name,pins):
    # pins = (number, label, electrical type, side). A single editable unit.
    sides={s:[p for p in pins if p[3]==s] for s in ['L','R']}
    h=max(len(v) for v in sides.values())*2.54/2+1.27
    sym=['symbol',Q(name),['pin_names',['offset',0.8]],['in_bom','yes'],['on_board','yes'],
         ['property',Q('Reference'),Q('U'),['at',0,h+2.54,0],effects()],
         ['property',Q('Value'),Q(name),['at',0,-h-2.54,0],effects()]]
    unit=['symbol',Q(name+'_1_1'),['rectangle',['start',-10.16,h],['end',10.16,-h],['stroke',['width',0.254],['type','default']],['fill',['type','background']]]]
    for side,ps in sides.items():
        for i,(num,label,typ,_) in enumerate(ps):
            x=-15.24 if side=='L' else 15.24
            y=(len(ps)-1)*1.27-i*2.54
            unit.append(['pin',typ,'line',['at',x,y,0 if side=='L' else 180],['length',5.08],['name',Q(label),effects(0.9)],['number',Q(str(num)),effects(0.9)]])
    sym.append(unit)
    return sym

def customs():
    ft_names={1:'OSCI',2:'OSCO',3:'VPHY',4:'AGND',5:'REF',6:'DM',7:'DP',8:'VPLL',9:'AGND',10:'GND',11:'GND',12:'VCCIO',13:'TXD',14:'RXD',15:'RTS#',16:'CTS#',17:'DTR# (unused)',18:'DSR# (unused)',19:'DCD# (unused)',20:'RI# (unused)',21:'ACBUS0',22:'GND',23:'GND',24:'VCCIO',25:'ACBUS1',26:'ACBUS2',27:'ACBUS3/RXLED#',28:'ACBUS4/TXLED#',29:'ACBUS5',30:'ACBUS6',31:'ACBUS7',32:'ACBUS8/PWREN#',33:'ACBUS9',34:'RESET#',35:'GND',36:'GND',37:'VCCA(1V8)',38:'VCORE(1V8)',39:'VCCD(3V3)',40:'VREGIN',41:'AGND',42:'TEST',43:'EEDATA',44:'EECLK',45:'EECS',46:'VCCIO',47:'GND',48:'GND'}
    left=[40,39,12,24,46,3,8,37,38,1,2,5,34,42,4,9,10,11,22,23,35,36,41,47,48]
    pins=[]
    for n in range(1,49):
        typ='bidirectional'
        if n in [3,4,8,9,10,11,12,22,23,24,35,36,39,40,41,46,47,48]:typ='power_in'
        if n in [37,38]:typ='power_out'
        if n in [1,5,14,16,18,19,20,31,34,42]:typ='input'
        if n in [2,13,15,17,27,28,32,44,45]:typ='output'
        pins.append((n,ft_names[n],typ,'L' if n in left else 'R'))
    axc=[(1,'VCCA','power_in','L'),(2,'1DIR','input','L'),(3,'2DIR','input','L'),(4,'1A1','bidirectional','L'),(5,'1A2','bidirectional','L'),(6,'2A1','bidirectional','L'),(7,'2A2','bidirectional','L'),(8,'GND','power_in','L'),(16,'VCCB','power_in','R'),(15,'1OE#','input','R'),(14,'2OE#','input','R'),(13,'1B1','bidirectional','R'),(12,'1B2','bidirectional','R'),(11,'2B1','bidirectional','R'),(10,'2B2','bidirectional','R'),(9,'GND','power_in','R')]
    return {s[1]:s for s in [custom('FT232HL_UART',pins),custom('SN74AXC4T245',axc),custom('USB_A_PLUG',[(1,'VBUS','passive','R'),(2,'D-','passive','R'),(3,'D+','passive','R'),(4,'GND','passive','R'),('SH','SHIELD','passive','R')]),custom('PCM13',[(1,'1V8/open','passive','L'),(2,'2V5','passive','L'),(4,'3V3','passive','L'),(3,'COMMON','passive','R')]),custom('PCM12',[(1,'OFF/open','passive','L'),(3,'ON/source','passive','L'),(2,'COMMON/out','passive','R')])]}

CUSTOM=customs(); CACHE={}
def library_symbol(libid):
    lib,name=libid.split(':')
    if lib=='A2':return copy.deepcopy(CUSTOM[name])
    if lib not in CACHE:
        root=parse((KICAD/'share/kicad/symbols'/f'{lib}.kicad_sym').read_text(encoding='utf-8'))
        CACHE[lib]={s[1]:s for s in children(root,'symbol')}
    src=copy.deepcopy(CACHE[lib][name]); ext=one(src,'extends')
    if ext:
        base=library_symbol(lib+':'+ext[1]); base[1]=Q(name)
        for unit in children(base,'symbol'):unit[1]=Q(re.sub(r'^.*?(_\d+_\d+)$',name+r'\1',unit[1]))
        props={p[1]:p for p in children(src,'property')}
        base=[x for x in base if not(isinstance(x,list) and x[0]=='property' and x[1] in props)]
        base.extend(props.values());src=base
    return src

def make_schematic():
    libs={p['lib']:library_symbol(p['lib']) for p in PARTS}
    libs['power:PWR_FLAG']=library_symbol('power:PWR_FLAG')
    sch=['kicad_sch',['version',20250114],['generator',Q('eeschema')],['uuid',Q(SCH_ID)],['paper',Q('A2')],
         ['title_block',['title',Q('A-2 USB UART / FT232H / 1.8-2.5-3.3V')],['date',Q('2026-11-19')],['rev',Q('A2-0.1 REVIEW')],['comment',1,Q('TXD RXD RTS CTS only. Do not fabricate before release review.')]]]
    embedded=['lib_symbols']
    for name,sym in libs.items():
        cp=copy.deepcopy(sym);cp[1]=Q(name);embedded.append(cp)
    sch.append(embedded)
    coords={'U1':(80,95),'U2':(195,75),'U3':(300,60),'U4':(400,60),'U5':(195,130),'U6':(300,120),'Q1':(400,120),'D1':(80,160),'J1':(35,30),'J2':(495,60),'J3':(550,60),'SW1':(495,125),'SW2':(350,165),'SW3':(450,165),'Y1':(150,175)}
    support=[p for p in PARTS if p['ref'] not in coords]
    for i,p in enumerate(support):coords[p['ref']]=(40+(i%10)*55,215+(i//10)*32)
    items=PARTS+[dict(ref=f'#FLG0{i+1}',value='PWR_FLAG',lib='power:PWR_FLAG',footprint='',nets={'1':n},mpn='',note='') for i,n in enumerate(FLAGS)]
    for i,n in enumerate(FLAGS):coords[f'#FLG0{i+1}']=(55+i*80,380)
    for p in items:
        ref=p['ref']; x,y=[round(round(v/1.27)*1.27,4) for v in coords[ref]]; sym=libs[p['lib']]; iid=uid(ref)
        inst=['symbol',['lib_id',Q(p['lib'])],['at',x,y,0],['unit',1],['in_bom','no' if ref.startswith('#') else 'yes'],['on_board','no' if ref.startswith('#') else 'yes'],['dnp','no'],['uuid',Q(iid)]]
        pinlist=[v for u in children(sym,'symbol') for v in children(u,'pin')]
        miny=min((-float(one(v,'at')[2]) for v in pinlist),default=-2.54)
        for unit in children(sym,'symbol'):
            for rect in children(unit,'rectangle'):
                miny=min(miny,-float(one(rect,'start')[2]),-float(one(rect,'end')[2]))
        for key,val,yy,hide in [('Reference',ref,y+miny-5.08,False),('Value',p['value'],y+miny-2.54,False),('Footprint','A2:'+p['footprint'].split(':')[-1] if p['footprint'] else '',y,True),('Datasheet','',y,True),('MPN',p['mpn'],y,True),('Note',p['note'],y,True)]:
            eff=effects(1.0)
            if hide:eff.append(['hide','yes'])
            prop_x=x
            if len(pinlist)<=4 and not ref.startswith(('SW','J','D')) and key in ['Reference','Value']:
                prop_x=x+6.35;yy=y+(-1.27 if key=='Reference' else 1.27);eff.append(['justify','left'])
            inst.append(['property',Q(key),Q(val),['at',prop_x,yy,0],eff])
        for pn in pinlist:
            num=one(pn,'number')[1]; inst.append(['pin',Q(num),['uuid',Q(uid(ref+':'+num))]])
            a=one(pn,'at'); px=x+float(a[1]);py=y-float(a[2]);angle=float(a[3]);net=p['nets'].get(num)
            if net is None:
                sch.append(['no_connect',['at',px,py],['uuid',Q(uid(ref+':nc:'+num))]])
            else:
                dx=-math.cos(math.radians(angle))*3.81;dy=math.sin(math.radians(angle))*3.81
                ex=round(px+dx,4);ey=round(py+dy,4)
                sch.append(['wire',['pts',['xy',px,py],['xy',ex,ey]],['stroke',['width',0],['type','default']],['uuid',Q(uid(ref+':wire:'+num))]])
                # Text extends away from the symbol, with upright labels.
                la=0 if angle in (0,180) else 90
                eff=effects(0.9);eff.append(['justify','right' if angle==0 else 'left','bottom'])
                sch.append(['label',Q(net),['at',ex,ey,la],eff,['uuid',Q(uid(ref+':label:'+num))]])
        inst.append(['instances',['project',Q('a2_usb_uart'),['path',Q('/'+SCH_ID),['reference',Q(ref)],['unit',1]]]])
        sch.append(inst)
    for x,y,t in [(270,25,'POWER: USB5V -> fixed 3V3 + adjustable VIO'),(180,25,'UART: two independent 2-bit directions'),(90,195,'DECOUPLING / FEEDBACK / EEPROM / INDICATORS'),(400,385,'SW1: change voltage only with USB unplugged'),(400,392,'J2 left-to-right: GND, TXD, RXD, USB5V_OUT'),(400,399,'J3: RTS#, CTS#, GND, VIO_OUT; no external power input')]:
        sch.append(['text',Q(t),['at',x,y,0],effects(1.27),['uuid',Q(uid(t))]])
    sch.append(['sheet_instances',['path',Q('/'),['page',Q('1')]]])
    (ROOT/'a2_usb_uart.kicad_sch').write_text(dump(sch),encoding='utf-8')
    local=['kicad_symbol_lib',['version',20250114],['generator',Q('kicad_symbol_editor')]]+list(CUSTOM.values())
    (ROOT/'libraries/A2.kicad_sym').write_text(dump(local),encoding='utf-8')

def mm(v):return pcb.FromMM(v)
def vec(x,y):return pcb.VECTOR2I(mm(x),mm(y))
def make_header(lib):
    f=pcb.FOOTPRINT(None); f.SetFPID(pcb.LIB_ID('A2','TSM_104_SH_PROVISIONAL')); f.SetAttributes(pcb.FP_SMD)
    f.SetLibDescription('Provisional 2.54 mm horizontal SMT header; confirm vendor land pattern before release')
    for i in range(4):
        p=pcb.PAD(f);p.SetNumber(str(i+1));p.SetAttribute(pcb.PAD_ATTRIB_SMD);p.SetShape(pcb.PAD_SHAPE_RECT);p.SetSize(vec(1.1,2.5));p.SetPosition(vec((i-1.5)*2.54,0));ls=pcb.LSET()
        for layer in [pcb.F_Cu,pcb.F_Paste,pcb.F_Mask]:ls.AddLayer(layer)
        p.SetLayerSet(ls);f.Add(p)
    for layer,x1,y1,x2,y2,w in [(pcb.F_Fab,-5.08,1.3,5.08,3.84,0.1),(pcb.F_CrtYd,-5.4,-1.55,5.4,10,0.05)]:
        s=pcb.PCB_SHAPE(f);s.SetShape(pcb.SHAPE_T_RECT);s.SetStart(vec(x1,y1));s.SetEnd(vec(x2,y2));s.SetWidth(mm(w));s.SetLayer(layer);f.Add(s)
    f.Reference().SetPosition(vec(0,-2));f.Reference().SetText('REF**')
    pcb.FootprintSave(str(lib),f)

def make_board():
    lib=ROOT/'libraries/A2.pretty';lib.mkdir(exist_ok=True)
    for p in PARTS:
        source,name=p['footprint'].split(':')
        if source!='A2':shutil.copyfile(KICAD/'share/kicad/footprints'/f'{source}.pretty'/f'{name}.kicad_mod',lib/f'{name}.kicad_mod')
    make_header(lib)
    b=pcb.BOARD();b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(mm(1.6))
    b.GetDesignSettings().m_MinClearance=mm(0.127);b.GetDesignSettings().m_CopperEdgeClearance=mm(0.25)
    nets={}
    for name in sorted({n for p in PARTS for n in p['nets'].values() if n}):
        n=pcb.NETINFO_ITEM(b,'/'+name);b.Add(n);nets[name]=n
    for p in PARTS:
        name=p['footprint'].split(':')[-1];f=pcb.FootprintLoad(str(lib),name)
        assert f is not None,name
        f.SetFPID(pcb.LIB_ID('A2',name)); f.SetReference(p['ref']);f.SetValue(p['value'])
        path=pcb.KIID_PATH();path.push_back(pcb.KIID(SCH_ID));path.push_back(pcb.KIID(uid(p['ref'])));f.SetPath(path)
        b.Add(f);f.SetPosition(vec(100+p['xy'][0],100+p['xy'][1]));f.SetOrientationDegrees(p['angle'])
        f.Value().SetVisible(False)
        f.Reference().SetTextSize(vec(0.65,0.65));f.Reference().SetTextThickness(mm(0.1));f.Reference().SetTextAngle(pcb.EDA_ANGLE(0,pcb.DEGREES_T))
        for pad in f.Pads():
            net=p['nets'].get(pad.GetNumber())
            if net:pad.SetNet(nets[net])
    for (a,c) in [((100,100),(122,100)),((122,100),(122,150)),((122,150),(100,150)),((100,150),(100,100))]:
        s=pcb.PCB_SHAPE();s.SetShape(pcb.SHAPE_T_SEGMENT);s.SetStart(vec(*a));s.SetEnd(vec(*c));s.SetWidth(mm(.05));s.SetLayer(pcb.Edge_Cuts);b.Add(s)
    b.GetDesignSettings().SetAuxOrigin(vec(100,150))
    pcb.SaveBoard(str(ROOT/'a2_usb_uart.kicad_pcb'),b)
    project={'meta':{'filename':'a2_usb_uart.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':0.127,'min_track_width':0.127,'min_via_diameter':0.5,'min_through_hole_diameter':0.25,'min_hole_to_hole':0.25,'min_copper_edge_clearance':0.25,'min_silk_clearance':0.1,'min_text_height':0.6,'min_text_thickness':0.1},'rule_severities':{}}},'net_settings':{'classes':[{'name':'Default','clearance':0.127,'track_width':0.18,'via_diameter':0.55,'via_drill':0.25,'diff_pair_width':0.3,'diff_pair_gap':0.15,'diff_pair_via_gap':0.25}],'meta':{'version':3}},'erc':{'erc_exclusions':[]},'schematic':{},'pcbnew':{}}
    (ROOT/'a2_usb_uart.kicad_pro').write_text(json.dumps(project,indent=2),encoding='utf-8')
    (ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "A2")(type "KiCad")(uri "${KIPRJMOD}/libraries/A2.pretty")(options "")(descr "A-2 frozen footprints")))\n',encoding='utf-8')
    stdlibs=sorted({p['lib'].split(':')[0] for p in PARTS if not p['lib'].startswith('A2:')}|{'power'})
    entries=['(lib (name "A2")(type "KiCad")(uri "${KIPRJMOD}/libraries/A2.kicad_sym")(options "")(descr "A-2 symbols"))']
    entries += [f'(lib (name "{n}")(type "KiCad")(uri "${{KICAD10_SYMBOL_DIR}}/{n}.kicad_sym")(options "")(descr ""))' for n in stdlibs]
    (ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) '+' '.join(entries)+')\n',encoding='utf-8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--replace-generated',action='store_true');args=ap.parse_args()
    if (ROOT/'a2_usb_uart.kicad_pcb').exists() and not args.replace_generated:raise SystemExit('Refusing to overwrite CAD. Review changes and backups first.')
    make_schematic();make_board()
    (ROOT/'reports/design_manifest.json').write_text(json.dumps(PARTS,indent=2),encoding='utf-8')
    with (ROOT/'reports/bom.csv').open('w',newline='',encoding='utf-8-sig') as fh:
        w=csv.writer(fh);w.writerow(['Reference','Value','MPN','Footprint','Notes'])
        for p in PARTS:w.writerow([p[k] for k in ['ref','value','mpn','footprint','note']])
    print(f'Generated native KiCad schematic/PCB: {len(PARTS)} components')
