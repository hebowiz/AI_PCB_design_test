"""A-1 authored circuit. Generate local atomic .ato parts and a reviewable net manifest.

Run using ordinary Python. This does not generate placement or copper and must
not be used to overwrite a human-edited PCB. See reports/design_review.md.
"""
import csv
import json
import os
from pathlib import Path
import shutil
import stat

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'board'
PARTS = BOARD / 'parts'
LIB = Path(os.environ['LOCALAPPDATA']) / 'Programs/KiCad/10.0/share/kicad/footprints'
components = []


def add(ref, name, value, mpn, maker, fp, nets, pos, pin_names=None, types=None, notes=''):
    nets = {str(k): v for k, v in nets.items()}
    components.append(dict(ref=ref, name=name, value=value, mpn=mpn,
        manufacturer=maker, footprint=fp, nets=nets, position=pos,
        pin_names={str(k): v for k, v in (pin_names or {}).items()},
        pin_types={str(k): v for k, v in (types or {}).items()}, notes=notes))


def r(ref, name, value, mpn, a, b, pos):
    add(ref, name, value, mpn, 'Yageo', 'Resistor_SMD:R_0402_1005Metric',
        {1:a, 2:b}, pos)


def c(ref, name, value, mpn, a, pos, size='0402'):
    fp = {'0402':'C_0402_1005Metric', '0603':'C_0603_1608Metric'}[size]
    add(ref, name, value, mpn, 'Murata', 'Capacitor_SMD:'+fp,
        {1:a, 2:'GND'}, pos)


# USB plug faces the negative Y short edge. Mechanical approval for the
# 1.6 mm PCB matches the Molex recommended thickness.
add('J1','usb','USB-A plug','0480372200','Molex',
    'Connector_USB:USB_A_Molex_48037-2200_Horizontal',
    {1:'VBUS',2:'USB_DM',3:'USB_DP',4:'GND','SH':'GND'}, [11,-6.4,90],
    notes='User changed A-1 thickness to 1.6 mm, matching the manufacturer recommendation.')

ftnames={1:'OSCI',2:'OSCO',3:'VPHY',4:'AGND',5:'REF',6:'DM',7:'DP',8:'VPLL',9:'AGND',
    10:'GND',11:'GND',12:'VCCIO',13:'TXD',14:'RXD',15:'RTS_N',16:'CTS_N',17:'DTR_N',
    18:'DSR_N',19:'DCD_N',20:'RI_N',21:'ACBUS0',22:'GND',23:'GND',24:'VCCIO',
    25:'ACBUS1',26:'ACBUS2',27:'RXLED_N',28:'TXLED_N',29:'ACBUS5',30:'PWREN_N',
    31:'PWRSAV_N',32:'ACBUS8',33:'ACBUS9',34:'RESET_N',35:'GND',36:'GND',37:'VCCA',
    38:'VCORE',39:'VCCD',40:'VREGIN',41:'AGND',42:'TEST',43:'EEDATA',44:'EECLK',45:'EECS',
    46:'VCCIO',47:'GND',48:'GND'}
ftnets={p:None for p in range(1,49)}
for p in [4,9,10,11,22,23,35,36,41,42,47,48]: ftnets[p]='GND'
for p in [12,24,46,39]: ftnets[p]='V3V3'
ftnets.update({1:'XI',2:'XO',3:'VPHY',5:'REF',6:'USB_DM',7:'USB_DP',8:'VPLL',
    13:'FT_TXD',14:'FT_RXD',15:'FT_RTS_N',16:'FT_CTS_N',18:'V3V3',19:'V3V3',20:'V3V3',
    27:'RXLED_N',28:'TXLED_N',30:'PWREN_N',31:'V3V3',34:'RESET_N',37:'VCCA_1V8',
    38:'VCORE_1V8',40:'VBUS_FT',43:'EEDATA',44:'EECLK',45:'EECS'})
fttypes={p:'bidirectional' for p in range(1,49)}
for p in [4,9,10,11,22,23,35,36,41,47,48,3,8,12,24,46,40]: fttypes[p]='power_in'
for p in [37,38,39]: fttypes[p]='power_out'
for p in [1,5,14,16,18,19,20,31,34,42]: fttypes[p]='input'
for p in [2,13,15,17,27,28,30,44,45]: fttypes[p]='output'
add('U1','ft232h','FT232HL','FT232HL-REEL','FTDI','Package_QFP:LQFP-48_7x7mm_P0.5mm',
    ftnets,[11,14,270],ftnames,fttypes)

add('U2','translator','SN74AXC4T245','SN74AXC4T245PWR','Texas Instruments',
    'Package_SO:TSSOP-16_4.4x5mm_P0.65mm',
    {1:'V3V3',2:'V3V3',3:'GND',4:'FT_TXD',5:'FT_RTS_N',6:'FT_RXD',7:'FT_CTS_N',
     8:'GND',9:'GND',10:'CTS_N',11:'RXD',12:'RTS_N',13:'TXD',14:'PWREN_N',15:'PWREN_N',16:'VIO'},
    [11,24,0],{1:'VCCA',2:'1DIR',3:'2DIR',4:'1A1',5:'1A2',6:'2A1',7:'2A2',8:'GND',
    9:'GND',10:'2B2',11:'2B1',12:'1B2',13:'1B1',14:'2OE_N',15:'1OE_N',16:'VCCB'},
    {1:'power_in',16:'power_in',8:'power_in',9:'power_in',2:'input',3:'input',4:'input',
    5:'input',6:'output',7:'output',10:'input',11:'input',12:'output',13:'output',14:'input',15:'input'})

add('U3','vio_ldo','TLV76701','TLV76701DRVR','Texas Instruments',
    'Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm',
    {1:'VIO',2:'FB',3:'GND',4:'VBUS',5:'GND',6:'VBUS',7:'GND'},[2.8,27,0],
    {1:'OUT',2:'FB',3:'GND',4:'EN',5:'GND',6:'IN',7:'EP'},
    {1:'power_out',2:'input',3:'power_in',4:'input',5:'power_in',6:'power_in',7:'power_in'})

add('U4','eeprom','93LC56B x16','93LC56BT-I/SN','Microchip',
    'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
    {1:'EECS',2:'EECLK',3:'EEDATA',4:'EEDO',5:'GND',6:None,7:None,8:'V3V3'},[3.0,19.4,90],
    {1:'CS',2:'CLK',3:'DI',4:'DO',5:'VSS',6:'NC',7:'NC',8:'VCC'},
    {1:'input',2:'input',3:'input',4:'tri_state',5:'power_in',6:'no_connect',7:'no_connect',8:'power_in'})

# 12 MHz ±10 ppm tolerance / ±10 ppm temperature option, CL=18 pF.
# 30 pF each with ~3 pF estimated stray; verify frequency on assembled PCB.
add('Y1','crystal','12MHz CL18pF','ABM8-12.000MHZ-B1U-T','Abracon',
    'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',
    {1:'XI',2:'GND',3:'XO',4:'GND'},[18.2,8.8,0])

# GND/TXD/RXD/USB5V left to right in top view; pins exit positive Y.
add('J2','uart_header','GND TXD RXD USB5V','TSM-104-01-L-SH','Samtec',
    'A1:TSM_104_SH',{1:'GND',2:'TXD',3:'RXD',4:'USB5V_OUT'},[11,44.717,0],
    notes='Locally drawn SMT right-angle footprint; manufacturer drawing review recorded separately.')
add('J3','aux_header','GND RTS CTS VIO','TSM-104-01-L-SV','Samtec',
    'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical_SMD_Pin1Left',
    {1:'GND',2:'RTS_N',3:'CTS_N',4:'VIO_OUT'},[11,39.4,90])

# DP3T row 1 selects extra FB-to-GND conductance; the 3.3V upper resistor
# and 1.8V default lower resistor remain connected during contact breaks.
add('SW1','voltage_select','1.8 / 2.5 / 3.3V','JS203011SCQN','C&K',
    'A1:JS203011SCQN',{1:None,2:'SEL_2V5',3:'GND',4:'SEL_3V3',5:None,6:None,7:None,8:None},
    [11,31.6,0], notes='Only switch with USB disconnected. Contact-break default is 1.8V.')
add('SW2','usb5v_switch','USB5V OFF/ON','PCM12SMTR','C&K','Button_Switch_SMD:SW_SPDT_PCM12',
    {1:'VBUS',2:'USB5V_OUT',3:None},[2.8,40.4,270])
add('SW3','vio_switch','VIO OUT OFF/ON','PCM12SMTR','C&K','Button_Switch_SMD:SW_SPDT_PCM12',
    {1:'VIO',2:'VIO_OUT',3:None},[19.2,40.4,90])

# Murata BLM15AG601SN1D, 600 ohm at 100MHz, 0402.
for ref,name,a,b,pos in [
    ('FB1','vbus_bead','VBUS','VBUS_FT',[3,5.8,90]),
    ('FB2','phy_bead','V3V3','VPHY',[16.7,5.8,90]),
    ('FB3','pll_bead','V3V3','VPLL',[5.5,6.1,0])]:
    add(ref,name,'600R@100MHz','BLM15AG601SN1D','Murata','Inductor_SMD:L_0402_1005Metric',{1:a,2:b},pos)

# 1005M (0402) except bulk capacitors, which use 1608M (0603).
cap100='GRM155R71C104KA88D'
cap1='GRM188R61A105KA61D'
cap47='GRM188R61A475KE15D'
for args in [
    ('C1','vbus_in','100nF 16V',cap100,'VBUS',[2,3.8,0],'0402'),
    ('C2','ft_bulk','4.7uF 10V',cap47,'VBUS_FT',[3,8.4,90],'0603'),
    ('C3','ft_vreg','100nF 16V',cap100,'VBUS_FT',[17.5,15.2,90],'0402'),
    ('C4','ft_3v3','1uF 10V',cap1,'V3V3',[17.5,17.6,90],'0603'),
    ('C5','ft_vcca','100nF 16V',cap100,'VCCA_1V8',[17.5,19.8,0],'0402'),
    ('C6','ft_vcore','100nF 16V',cap100,'VCORE_1V8',[20.5,18.5,90],'0402'),
    ('C7','ft_io12','100nF 16V',cap100,'V3V3',[5,8.5,90],'0402'),
    ('C8','ft_io24','100nF 16V',cap100,'V3V3',[4.8,12,90],'0402'),
    ('C9','ft_io46','100nF 16V',cap100,'V3V3',[17.5,11.9,90],'0402'),
    ('C10','phy_dec','100nF 16V',cap100,'VPHY',[15,7.6,0],'0402'),
    ('C11','pll_dec','100nF 16V',cap100,'VPLL',[7,7.8,90],'0402'),
    ('C12','x1_load','30pF C0G 50V','GRM1555C1H300JA01D','XI',[18.5,5.7,0],'0402'),
    ('C13','x2_load','30pF C0G 50V','GRM1555C1H300JA01D','XO',[20.8,8.8,90],'0402'),
    ('C14','level_a','100nF 16V',cap100,'V3V3',[7.4,20.8,0],'0402'),
    ('C15','level_b','100nF 16V',cap100,'VIO',[14.8,20.8,0],'0402'),
    ('C16','eeprom_dec','100nF 16V',cap100,'V3V3',[3.8,14.5,0],'0402'),
    ('C17','ldo_in','1uF 10V',cap1,'VBUS',[4.4,24.2,0],'0603'),
    ('C18','ldo_out','4.7uF 10V',cap47,'VIO',[1.7,29.5,0],'0603'),
]: c(*args)

r('R1','ref_res','12k 1%','RC0402FR-0712KL','REF','GND',[15.3,9.4,90])
r('R2','reset_pullup','10k 1%','RC0402FR-0710KL','RESET_N','V3V3',[11.5,20,0])
r('R3','eeprom_do_series','2.2k 1%','RC0402FR-072K2L','EEDATA','EEDO',[1.2,10.8,90])
r('R4','eeprom_do_pullup','10k 1%','RC0402FR-0710KL','V3V3','EEDO',[1.2,13.1,90])
r('R5','oe_pullup','10k 1%','RC0402FR-0710KL','V3V3','PWREN_N',[17,21.7,90])
r('R6','rx_pullup','47k 1%','RC0402FR-0747KL','VIO','RXD',[18,25,0])
r('R7','cts_pullup','47k 1%','RC0402FR-0747KL','VIO','CTS_N',[18.5,26.4,0])
# VOUT=.8*(1+100k/Rbottom): 1.793V, 2.501V, 3.285V nominal.
r('R8','fb_top','100k 0.1%','RT0402BRD07100KL','VIO','FB',[2.2,31.1,0])
r('R9','fb_bottom','80.6k 0.1%','RT0402BRD0780K6L','FB','GND',[1.2,33.1,90])
r('R10','fb_2v5','113k 0.1%','RT0402BRD07113KL','FB','SEL_2V5',[3,33,90])
r('R11','fb_3v3','53.6k 0.1%','RT0402BRD0753K6L','FB','SEL_3V3',[19,33,90])
r('R12','power_led_res','6.8k 1%','RC0402FR-076K8L','VBUS','PWR_LED_A',[19,3.8,90])
r('R13','tx_led_res','3.3k 1%','RC0402FR-073K3L','V3V3','TX_LED_A',[18.8,12.1,90])
r('R14','rx_led_res','3.3k 1%','RC0402FR-073K3L','V3V3','RX_LED_A',[18.8,15.0,90])
add('D1','power_led','Red 1608M','LTST-C190KRKT','Lite-On','LED_SMD:LED_0603_1608Metric',
    {1:'GND',2:'PWR_LED_A'},[20.3,2.2,90],{1:'K',2:'A'})
add('D2','tx_led','Green 1608M','LTST-C190KGKT','Lite-On','LED_SMD:LED_0603_1608Metric',
    {1:'TXLED_N',2:'TX_LED_A'},[20.8,12.3,90],{1:'K',2:'A'})
add('D3','rx_led','Green 1608M','LTST-C190KGKT','Lite-On','LED_SMD:LED_0603_1608Metric',
    {1:'RXLED_N',2:'RX_LED_A'},[20.8,15.4,90],{1:'K',2:'A'})
# Low-capacitance ESD clamps. TPD1E05U06 DYA pin 1=IO, pin 2=GND.
for ref,name,net,pos in [('D4','usb_dm_esd','USB_DM',[9.3,7.1,180]),('D5','usb_dp_esd','USB_DP',[12.7,7.2,0])]:
    add(ref,name,'USB ESD 0.5pF','TPD1E05U06DYAR','Texas Instruments','Diode_SMD:D_SOD-523',
        {1:net,2:'GND'},pos,{1:'IO',2:'GND'})


def main():
    PARTS.mkdir(exist_ok=True, parents=True)
    # Custom footprints transcribed from manufacturer mechanical drawings.
    def footprint(name, pads, body, courtyard, descr):
        x,y=body; cx,cy=courtyard
        lines=[f'(footprint "{name}" (version 20241229) (generator "A1") (layer "F.Cu")',
            f'(descr "{descr}") (attr smd)',
            f'(property "Reference" "REF**" (at 0 {-cy-0.8} 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))',
            f'(property "Value" "{name}" (at 0 {cy+0.8} 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))',
            f'(fp_rect (start {-x} {-y}) (end {x} {y}) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))',
            f'(fp_rect (start {-cx} {-cy}) (end {cx} {cy}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))']
        for n,px,py,w,h in pads:
            lines += [f'(pad "{n}" smd rect (at {px} {py}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask"))']
        lines += [')']
        (PARTS/(name+'.kicad_mod')).write_text('\n'.join(lines),encoding='utf-8')
    footprint('JS203011SCQN',[(i+1,x,2.5,1.2,3) for i,x in enumerate([-4,-2,2,4])]+
        [(i+5,x,-2.5,1.2,3) for i,x in enumerate([-4,-2,2,4])],
        (6.5,1.8),(6.75,4.25),'C&K JS203011SCQN; drawing JS series I-51, 2019-11-11; pin 3/7 common')
    footprint('TSM_104_SH',[(i+1,(i-1.5)*2.54,0,1.27,3.18) for i in range(4)],
        (5.08,1.52),(5.33,1.84),'Samtec TSM SH footprint rev B 2022-06-07; pad center is 5.283 mm inside board edge')
    # Move header body to the connector edge; courtyard spans pads and body.
    p=PARTS/'TSM_104_SH.kicad_mod'
    s=p.read_text().replace('(start -5.08 -1.52) (end 5.08 1.52)',
        '(start -5.08 2.235) (end 5.08 5.283)')
    s=s.replace('(start -5.33 -1.84) (end 5.33 1.84)',
        '(start -5.33 -1.84) (end 5.33 5.533)')
    p.write_text(s,encoding='utf-8')
    # Standard library copies retain the KiCad attribution in reports.
    for comp in components:
        lib, fp = comp['footprint'].split(':')
        dest = PARTS / (fp+'.kicad_mod')
        if lib != 'A1':
            if dest.exists(): dest.chmod(stat.S_IWRITE | stat.S_IREAD)
            shutil.copyfile(LIB/(lib+'.pretty')/(fp+'.kicad_mod'),dest)
    (BOARD/'design.json').write_text(json.dumps(dict(
        board=dict(width_mm=22,height_mm=50,thickness_mm=1.6,copper_layers=2),
        components=components),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    ato=['# Authored A-1 circuit; generated by scripts/design.py.',
         'import has_designator','import has_net_name','import RectangularBoardShape']
    defs=['import is_atomic_part','import has_designator_prefix']
    for comp in components:
        cls='Part_'+comp['ref']
        fp=comp['footprint'].split(':')[1]
        defs += ['',f'component {cls}:',
            f'    trait is_atomic_part<manufacturer="{comp["manufacturer"]}", partnumber="{comp["mpn"]}", footprint="{fp}.kicad_mod", symbol="">',
            f'    trait has_designator_prefix<prefix="{comp["ref"].rstrip("0123456789")}">']
        for pin in comp['nets']:
            defs += [f'    signal p{pin} ~ pin {pin}' if pin.isdigit() else f'    signal p{pin} ~ pin "{pin}"']
        ato += [f'from "parts/parts.ato" import {cls}']
    ato += ['', 'module A1:', '    outline = new RectangularBoardShape',
        '    outline.x = 22mm','    outline.y = 50mm','    outline.corner_radius = 0mm']
    nets=sorted({n for comp in components for n in comp['nets'].values() if n})
    for net in nets:
        ato += [f'    signal {net}',f'    trait {net} has_net_name<name="{net}">']
    for comp in components:
        name=comp['name']
        ato += ['', f'    {name} = new Part_{comp["ref"]}',
            f'    trait {name} has_designator<designator="{comp["ref"]}">']
        for pin,net in comp['nets'].items():
            if net: ato += [f'    {net} ~ {name}.p{pin}']
    (PARTS/'parts.ato').write_text('\n'.join(defs)+'\n',encoding='utf-8')
    (BOARD/'main.ato').write_text('\n'.join(ato)+'\n',encoding='utf-8')
    with (ROOT/'reports/bom.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f)
        writer.writerow(['Reference','Instance','Value','Manufacturer','MPN','Footprint','Quantity','Notes'])
        writer.writerows([[x['ref'],x['name'],x['value'],x['manufacturer'],x['mpn'],x['footprint'],1,x['notes']] for x in components])
    print(f'Wrote {len(components)} atomic components; {len(nets)} named nets.')


if __name__ == '__main__': main()
