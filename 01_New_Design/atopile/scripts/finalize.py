"""Save per-instance derived library footprints and document final copper.
The authored atomic source remains unchanged. These footprints include reviewed
silkscreen relocation and direct ground connections on five pads.
"""
import json,os,sys
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1]
b=k.LoadBoard(str(ROOT/'board/a1.kicad_pcb'));lib=ROOT/'board/A1.pretty';lib.mkdir(exist_ok=True)
for f in b.GetFootprints():
    ref=f.GetReference();f.SetFPID(k.LIB_ID('A1',ref));k.PCB_IO_KICAD_SEXPR().FootprintSave(str(lib),f)
k.SaveBoard(str(ROOT/'board/a1.kicad_pcb'),b)
(ROOT/'board/fp-lib-table').write_text('''(fp_lib_table (version 7)
 (lib (name "parts") (type "KiCad") (uri "${KIPRJMOD}/parts") (options "") (descr "Original A-1 atomic footprint inputs"))
 (lib (name "A1") (type "KiCad") (uri "${KIPRJMOD}/A1.pretty") (options "") (descr "A-1 derived footprints: silk and ground-pad connections")))
''')
print('Saved 51 final derived footprints.');sys.stdout.flush();os._exit(0)
