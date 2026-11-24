from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'reports/pcb_power_polish'
CLI=Path.home()/'AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe'
for stage in ['before','after']:
 board=OUT/'before/a2_usb_uart.kicad_pcb' if stage=='before' else OUT/'candidate/a2_usb_uart.kicad_pcb'
 for side,layers in [('front','F.Cu,F.SilkS,Edge.Cuts'),('back','B.Cu,B.SilkS,Edge.Cuts'),('placement','F.Fab,F.SilkS,Edge.Cuts')]:
  cmd=[str(CLI),'pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--layers',layers,'-o',str(OUT/stage/(side+'.svg')),str(board)]
  if side=='back':cmd.insert(4,'--mirror')
  subprocess.run(cmd,check=True)

# Normalize KiCad export whitespace, preserving drawing geometry.
for file in OUT.glob("*/*.svg"):
 file.write_text("\n".join(line.rstrip() for line in file.read_text().splitlines()).rstrip()+"\n")
