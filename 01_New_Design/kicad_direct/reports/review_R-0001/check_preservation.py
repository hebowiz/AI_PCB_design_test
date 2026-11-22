from pathlib import Path
import sys,json,subprocess,hashlib,platform,datetime,csv
from PIL import Image
H=Path(__file__).resolve().parent; R=H.parents[1]; ROOT=R.parents[1]
sys.path.insert(0,str(R/'scripts'));from sexpr import *
base='778ab8896a4f9b71efba0c45f701cbf2fdfc2cac';rel='01_New_Design/kicad_direct/a2_usb_uart.kicad_sch'
a=parse((H/'before/a2_usb_uart.kicad_sch').read_text());b=parse((ROOT/rel).read_text());m=json.loads((H/'patch.json').read_text())
old={str(one(w,'uuid')[1]):w for w in children(a,'wire')};new={str(one(w,'uuid')[1]):w for w in children(b,'wire')}
checks={'only_three_old_wires_removed':set(old)-set(new)==set(m['removed_wire_uuids']),'all_retained_wires_equal':all(old[k]==new[k] for k in old if k in new),'four_new_wires':len(set(new)-set(old))==4,'junctions_labels_no_connects_preserved':all(children(a,k)==children(b,k) for k in ['junction','label','global_label','no_connect','bus','bus_entry']),'sheet_root_and_paper_preserved':all(one(a,k)==one(b,k) for k in ['uuid','paper'])}
for version in ('before','after'):
 man=json.loads((H/version/'manifest.json').read_text())
 checks[version+'_export_hashes_match']=all(hashlib.sha256((H/version/f).read_bytes()).hexdigest()==s for f,s in man['files'].items())
lines=subprocess.check_output(['git','ls-tree','-r',base],cwd=ROOT,text=True).splitlines();original={}
for l in lines:
 meta,path=l.split('\t',1)
 if path!=rel and not path.startswith('01_New_Design/kicad_direct/reports/review_R-0001/'):original[path]=meta.split()[2]
paths=list(original)
proc=subprocess.run(['git','hash-object','--stdin-paths'],input='\n'.join(paths)+'\n',cwd=ROOT,text=True,capture_output=True,check=True)
hashes=proc.stdout.splitlines();assert len(hashes)==len(paths)
rows=[{'path':p,'base_git_blob':original[p],'working_git_blob':h,'equal':original[p]==h} for p,h in zip(paths,hashes)]
checks['all_protected_tracked_files_identical']=all(r['equal'] for r in rows)
with (H/'protected_files.csv').open('w',newline='',encoding='utf8') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
(H/'preservation.json').write_text(json.dumps({'checks':checks,'all_pass':all(checks.values()),'protected_file_count':len(rows),'system':platform.platform(),'python':sys.version,'at':datetime.datetime.now().astimezone().isoformat()},indent=2))
im=Image.open(H/'after/schematic.png');f=im.width/(594/1.27);im.crop(tuple(round(c*f) for c in (340,166,458,277))).save(H/'after/revision_notes.png')
print(json.dumps({'checks':checks,'protected_file_count':len(rows)},indent=2));assert all(checks.values())
