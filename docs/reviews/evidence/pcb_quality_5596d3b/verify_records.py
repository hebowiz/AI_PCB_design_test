"""Verify documentation update against registration commit and protect existing worktrees."""
from pathlib import Path
import ast,subprocess,hashlib,json,re
ROOT=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
# Parents: evidence directory -> evidence -> reviews -> docs -> repository.
assert (ROOT/'docs/reviews/review_register.md').exists()
def git(path,*args):return subprocess.check_output(['git',*args],cwd=path,text=True).strip()
def rows(text):
 result={}
 for l in text.splitlines():
  if not l.startswith('|'):continue
  r=[x.strip() for x in l.strip().strip('|').split('|')];m=re.search(r'R-\d{4}',r[0])
  if not m:continue
  assert len(r)==15;assert m[0] not in result;result[m[0]]=r
 return result
base='b8a48da1c7385c60c8789909a0630acaad9d2a95'
old=rows(subprocess.check_output(['git','show',base+':docs/reviews/review_register.md'],cwd=ROOT).decode());new=rows((ROOT/'docs/reviews/review_register.md').read_text(encoding='utf-8-sig'))
assert list(new)==[f'R-{i:04}' for i in range(1,33)]
for i in range(1,28):assert old[f'R-{i:04}']==new[f'R-{i:04}']
for i in range(28,33):
 for j in range(15):
  if j not in [8,14]:assert old[f'R-{i:04}'][j]==new[f'R-{i:04}'][j]
assert all(new[f'R-{i:04}'][9:11]==['完了','OK'] for i in range(1,17))
assert all(new[f'R-{i:04}'][9:11]==['保留','保留'] for i in range(17,28))
assert all(new[f'R-{i:04}'][9:11]==['調査中','未判定'] for i in range(28,33))
mainpro=ROOT/'01_New_Design/kicad_direct/a2_usb_uart.kicad_pro';prohash=hashlib.sha256(mainpro.read_bytes()).hexdigest();assert prohash=='e5b768239d2eb761331199dc0d3ef02ef9c2289797037a22e0de9d5ca595767d'
src=Path('C:/Users/hebow/.codex/worktrees/a2-pcb-review/99_AI_PCB_design_test');fixed=ROOT/'workspaces/A-2';PCB='01_New_Design/kicad_direct/a2_usb_uart.kicad_pcb';sha='5596d3bc8802687b89b21fd9c57e1117ec9382e5'
assert git(src,'rev-parse','HEAD')==sha;assert git(fixed,'rev-parse','HEAD')==sha
assert git(src,'status','--porcelain','--untracked-files=no')=='';assert git(fixed,'status','--porcelain','--untracked-files=no')==''
bhash=hashlib.sha256((src/PCB).read_bytes()).hexdigest();assert bhash=='d55cc3e2146be62a39707161abc60ae3331315a21a19285f17e98840de278c94'
assert hashlib.sha256((fixed/PCB).read_bytes()).hexdigest()==bhash
broken=[]
for f in [ROOT/'docs/reviews/batches/2026-11-24_R-0028_R-0032_investigation.md',P/'README.md']:
 for link in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8-sig')):
  if '://' in link or link.startswith('#') or link=='preservation.json':continue
  if not (f.parent/link.split('#')[0]).exists():broken.append((str(f),link))
assert not broken,broken
for f in P.glob('*.py'):ast.parse(f.read_text(encoding='utf-8-sig'))
subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
result={'register_base':base,'rows':32,'columns':15,'R0001_R0027_all_cells_unchanged_since_registration':True,'R0028_R0032_only_action_and_evidence_changed':True,'R0001_R0016_completed_OK':16,'R0017_R0027_hold':11,'R0028_R0032_investigating_unjudged':5,'source_and_fixed_commit':sha,'source_and_fixed_tracked_changes':False,'source_and_fixed_pcb_sha256':bhash,'preexisting_main_project_sha256_unchanged':prohash,'local_report_links_broken':broken,'python_syntax':'pass','git_diff_check':'pass','analysis_not_approved_skill':True}
(P/'preservation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
