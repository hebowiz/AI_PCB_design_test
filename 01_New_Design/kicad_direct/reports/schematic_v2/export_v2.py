"""Export the current V2 schematic without changing it or the project settings."""
from pathlib import Path
import os,subprocess,hashlib,json,datetime
H=Path(__file__).resolve().parent;R=H.parents[1];REPO=R.parents[1]
cli=Path(os.environ['LOCALAPPDATA'])/'Programs/KiCad/10.0/bin/kicad-cli.exe'
source=R/'a2_usb_uart.kicad_sch';out=H/'after'
sha=lambda b:hashlib.sha256(b).hexdigest()
records=[];source_hash=sha(source.read_bytes())
commands=[
 [str(cli),'sch','export','netlist','--format','kicadxml','-o',str(out/'netlist.xml'),str(source)],
 [str(cli),'sch','erc','--format','json','--exit-code-violations','-o',str(out/'erc.json'),str(source)],
 [str(cli),'sch','export','pdf','--black-and-white','-o',str(out/'schematic.pdf'),str(source)],
 ['pdftoppm','-scale-to','5600','-png','-singlefile',str(out/'schematic.pdf'),str(out/'detail_source')],
 ['pdftoppm','-scale-to','4200','-png','-singlefile',str(out/'schematic.pdf'),str(out/'schematic')]]
# Use the same relative source path as the V0 export so full XML equality is meaningful.
commands=[[str(Path(a).relative_to(REPO)) if Path(a).is_absolute() and Path(a).is_relative_to(REPO) else a for a in cmd] for cmd in commands]
for cmd in commands:
 t=datetime.datetime.now().astimezone().isoformat()
 p=subprocess.run(cmd,cwd=REPO,capture_output=True)
 records.append({'started':t,'command':cmd,'exit_code':p.returncode,'stdout':p.stdout.decode('utf-8',errors='replace'),'stderr':p.stderr.decode('utf-8',errors='replace')})
 (H/'export_log.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
 if p.returncode:raise SystemExit(f'Export failed: {cmd}')
assert sha(source.read_bytes())==source_hash
(out/'source_sha256.txt').write_text(source_hash+'\n')
manifest={'source_sha256':source_hash,'completed':datetime.datetime.now().astimezone().isoformat(),
 'outputs_sha256':{n:sha((out/n).read_bytes()) for n in ['netlist.xml','erc.json','schematic.pdf','schematic.png','detail_source.png']}}
(out/'export_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Exported XML/ERC/PDF/PNG; source hash recorded.')
