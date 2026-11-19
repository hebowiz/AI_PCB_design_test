"""Generate a pin-explicit KiCad review schematic from the authored manifest.
The symbols use declared electrical types; they are not vendor symbol assets.
Net labels make every pad assignment visible. ERC does not validate firmware or SI.
"""
import json
import math
from pathlib import Path
import uuid
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'board/design.json').read_text(encoding='utf-8'))
uid=lambda:str(uuid.uuid4())
q=lambda s:json.dumps(str(s),ensure_ascii=False)
font='(effects (font (size 1.0 1.0)))'

def main():
    rootid=uid(); libs=[]; bodies=[]
    # A2 sheet. First row: ICs. Other rows: connectors, power and passives.
    cs=DATA['components']; cs=sorted(cs,key=lambda c:(0 if c['ref'].startswith('U') else 1))
    for idx,c in enumerate(cs):
        n=len(c['nets']); half=math.ceil(n/2); h=max(7.62,(half+1)*2.54)
        col=idx%6; row=idx//6; x=round((45+col*92)/1.27)*1.27
        y=round((110+(row-1)*36 if row else 57)/1.27)*1.27
        ref=c['ref']; symbol='A1:'+ref; w=12.7
        pins=[]; instanceid=uid(); instpins=[]
        for i,(pin,net) in enumerate(c['nets'].items()):
            left=i<half; j=i if left else i-half
            px=-w-2.54 if left else w+2.54; py=h/2-2.54*(j+1)
            typ=c['pin_types'].get(pin,'passive'); name=c['pin_names'].get(pin,pin)
            pins.append(f'(pin {typ} line (at {px} {py} {0 if left else 180}) (length 2.54) (name {q(name)} {font}) (number {q(pin)} {font}))')
            gx=x+px; gy=y-py
            instpins.append(f'(pin {q(pin)} (uuid {uid()}))')
            if net:
                ex=gx-5.08 if left else gx+5.08
                bodies.append(f'(wire (pts (xy {gx} {gy}) (xy {ex} {gy})) (stroke (width 0) (type default)) (uuid {uid()}))')
                bodies.append(f'(label {q(net)} (at {ex} {gy} {0 if left else 180}) (effects (font (size 0.9 0.9)) (justify {"left" if left else "right"} bottom)) (uuid {uid()}))')
            else:
                bodies.append(f'(no_connect (at {gx} {gy}) (uuid {uid()}))')
        libs.append(f'''(symbol {q(symbol)} (pin_names (offset 0.5)) (in_bom yes) (on_board yes)
            (property "Reference" {q(ref)} (at 0 {h/2+2.54} 0) {font})
            (property "Value" {q(c['value'])} (at 0 {-h/2-2.54} 0) {font})
            (symbol "{ref}_0_1" (rectangle (start {-w} {h/2}) (end {w} {-h/2}) (stroke (width 0.254) (type default)) (fill (type background))))
            (symbol "{ref}_1_1" {' '.join(pins)}))''')
        bodies.append(f'''(symbol (lib_id {q(symbol)}) (at {x} {y} 0) (unit 1)
            (in_bom yes) (on_board yes) (dnp no) (uuid {instanceid})
            (property "Reference" {q(ref)} (at {x} {y-h/2-2.54} 0) {font})
            (property "Value" {q(c['value'])} (at {x} {y+h/2+2.54} 0) {font})
            (property "Footprint" {q('A1:'+ref)} (at {x} {y} 0) (effects (font (size 1 1)) hide))
            (property "MPN" {q(c['mpn'])} (at {x} {y} 0) (effects (font (size 1 1)) hide))
            {' '.join(instpins)}
            (instances (project "a1" (path "/{rootid}" (reference {q(ref)}) (unit 1)))))''')
    # Explicit supply origins: USB host VBUS/GND, and outputs of passive beads.
    # These flags only inform ERC; they do not assert measured voltage/current.
    flagsym='''(symbol "A1:PWR_FLAG" (power) (pin_names (offset 0)) (in_bom no) (on_board no)
      (property "Reference" "#FLG" (at 0 2.54 0) (effects (font (size 1 1)) hide))
      (property "Value" "PWR_FLAG" (at 0 3.81 0) (effects (font (size 1 1))))
      (symbol "PWR_FLAG_0_1" (polyline (pts (xy -1.27 1.27) (xy 0 2.54) (xy 1.27 1.27) (xy 0 0) (xy -1.27 1.27)) (stroke (width 0) (type default)) (fill (type none))))
      (symbol "PWR_FLAG_1_1" (pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 1 1)))) (number "1" (effects (font (size 1 1)))))))'''
    libs.append(flagsym)
    for i,net in enumerate(['VBUS','GND','VBUS_FT','VPHY','VPLL']):
        x=50.8+50.8*i; y=393.7; ref=f'#FLG0{i+1}'
        bodies.append(f'''(symbol (lib_id "A1:PWR_FLAG") (at {x} {y} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {uid()})
        (property "Reference" "{ref}" (at {x} {y} 0) (effects (font (size 1 1)) hide))
        (property "Value" "PWR_FLAG" (at {x} {y-3.81} 0) {font})
        (pin "1" (uuid {uid()})) (instances (project "a1" (path "/{rootid}" (reference "{ref}") (unit 1)))))
        (label "{net}" (at {x} {y} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid {uid()}))''')
    (ROOT/'board/A1.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "A1") '+ ' '.join(libs).replace('(symbol "A1:','(symbol "')+')',encoding='utf-8')
    (ROOT/'board/sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "A1") (type "KiCad") (uri "${KIPRJMOD}/A1.kicad_sym") (options "") (descr "A-1 authored review symbols")))',encoding='utf-8')
    text=f'''(kicad_sch (version 20250114) (generator "A1") (uuid {rootid}) (paper "A2")
    (title_block (title "A-1 USB UART: pin/net review") (date "2026-11-19") (rev "0.1")
    (comment 1 "TXD/RXD/RTS/CTS; 22 x 50 mm; 1.6 mm; all components front")
    (comment 2 "Engineering review only: USB and bead-output supply flags; see ERC scope"))
    (lib_symbols {' '.join(libs)}) {' '.join(bodies)}
    (sheet_instances (path "/" (page "1"))))'''
    (ROOT/'board/a1.kicad_sch').write_text(text,encoding='utf-8')
    print('Generated pin-explicit schematic:',len(cs),'symbols.')

if __name__=='__main__':main()
