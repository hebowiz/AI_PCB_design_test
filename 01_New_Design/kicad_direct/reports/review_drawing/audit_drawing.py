"""Validate exported electrical data and the five approved drawing changes."""
from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET,subprocess
H=Path(__file__).resolve().parent;R=H.parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(R/'scripts'));from sexpr import *
g=lambda a:tuple(round(float(v)/1.27,5) for v in a)
def read(v):
 s=parse((H/v/'a2_usb_uart.kicad_sch').read_text());objs={next(str(p[2]) for p in children(o,'property') if p[1]=='Reference'):o for o in children(s,'symbol')};w={frozenset(g(p[1:3]) for p in one(o,'pts')[1:]) for o in children(s,'wire')};return s,objs,w
sa,oa,wa=read('before');sb,ob,wb=read('after')
pos=lambda o:g(one(o,'at')[1:3])
def canonical(v):
 x=ET.parse(H/v/'netlist.xml')
 def node(e):return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),sorted([node(c) for c in e],key=repr)]
 return {'components':sorted([node(e) for e in x.findall('.//components/comp')],key=repr),'libparts':sorted([node(e) for e in x.findall('.//libparts/libpart')],key=repr),'nets':{e.get('name'):sorted([sorted(n.attrib.items()) for n in e.findall('node')],key=repr) for e in x.findall('.//nets/net')}}
a,b=canonical('before'),canonical('after');(H/'canonical_netlist_before.json').write_text(json.dumps(a,indent=2));(H/'canonical_netlist_after.json').write_text(json.dumps(b,indent=2))
def has(w,path):return all(frozenset((p,q)) in w for p,q in zip(path,path[1:]))
def cross(p,q):
 out=[]
 for a,b in zip(p,p[1:]):
  for c,d in zip(q,q[1:]):
   if a[0]==b[0] and c[1]==d[1] and min(a[1],b[1])<c[1]<max(a[1],b[1]) and min(c[0],d[0])<a[0]<max(c[0],d[0]):out.append((a[0],c[1]))
   if a[1]==b[1] and c[0]==d[0] and min(c[1],d[1])<a[1]<max(c[1],d[1]) and min(a[0],b[0])<c[0]<max(a[0],b[0]):out.append((c[0],a[1]))
 return out
old=[[(42,48),(58,48),(58,29),(187,29),(187,67),(177,67)],[(42,46),(74,46),(74,27),(189,27),(189,65),(177,65)],[(102,42),(93,42),(93,32),(137,32),(137,63),(153,63)],[(108,42),(117,42),(117,34),(139,34),(139,65),(153,65)]]
new=[[(42,48),(58,48),(58,27),(189,27),(189,67),(177,67)],[(42,46),(74,46),(74,29),(187,29),(187,65),(177,65)],[(102,42),(93,42),(93,32),(139,32),(139,63),(153,63)],[(108,42),(117,42),(117,34),(137,34),(137,65),(153,65)]]
checks={'canonical_netlists_identical':a==b,'all_old_and_new_pair_segments_present':all(has(w,p) for w,ps in [(wa,old),(wb,new)] for p in ps),'C3_feed_order':has(wb,[(130,79),(130,81),(134,81),(153,81)]) and has(wb,[(134,81),(134,82)]) and pos(ob['C3'])==(134,85),'USB5V_feed_order':has(wb,[(122,135),(130,135),(142,135),(146,135),(146,101),(151,101),(153,101)]) and pos(ob['C1'])==(130,138) and pos(ob['C23'])==(142,138),'C3_C1_C23_ground_below':all(pos(ob[gnd])[0]==pos(ob[cap])[0] and pos(ob[gnd])[1]>pos(ob[cap])[1] and float(one(ob[cap],'at')[3])==0 for cap,gnd in [('C3','#PWR0151'),('C1','#PWR0149'),('C23','#PWR0176')]),'FLAG_on_horizontal_line':pos(ob['#FLG07'])==(136,100) and has(wb,[(130,100),(136,100),(141,100)]),'FLAG_has_no_stem_wire_overlap':not any(len(w)==2 and all(p[0]==136 for p in w) and min(p[1] for p in w)<100 and max(p[1] for p in w)>98 for w in wb),'pair_crossing_targets':len(cross(new[0],new[1]))==1 and len(cross(new[2],new[3]))==0,'unchanged_ESD_positions':all(oa[r]==ob[r] for r in ['D1','D5','J1']),'live_source_matches_export':(R/'a2_usb_uart.kicad_sch').read_bytes()==(H/'after/a2_usb_uart.kicad_sch').read_bytes()}
refs=[r for r,o in oa.items() if pos(o)[0]<235 and pos(o)[1]>170]
def bounds(objs):
 ps=[pos(objs[r]) for r in refs];return [min(p[0] for p in ps),min(p[1] for p in ps),max(p[0] for p in ps),max(p[1] for p in ps)]
ba,bb=bounds(oa),bounds(ob);sizes=lambda b:[round((b[2]-b[0])*1.27,2),round((b[3]-b[1])*1.27,2)]
manifest=json.loads((H/'export_manifest.json').read_text());checks['export_hashes_match']=all(hashlib.sha256((H/p).read_bytes()).hexdigest()==v for p,v in manifest.items())
existing=set(subprocess.check_output(['git','ls-tree','-r','--name-only','886ad5428d4be98768ccc8bb942aa2f54f23d942'],cwd=ROOT,text=True).splitlines());diff=subprocess.check_output(['git','diff','--name-only','886ad5428d4be98768ccc8bb942aa2f54f23d942'],cwd=ROOT,text=True).splitlines();checks['only_existing_schematic_changed']=[p for p in diff if p in existing]==['01_New_Design/kicad_direct/a2_usb_uart.kicad_sch']
result={'checks':checks,'all_pass':all(checks.values()),'pair_crossings':{'before_USB':cross(old[0],old[1]),'after_USB':cross(new[0],new[1]),'before_XTAL':cross(old[2],old[3]),'after_XTAL':cross(new[2],new[3])},'power_symbol_center_bounds_grid':{'before':ba,'after':bb},'power_symbol_center_extent_mm':{'before':sizes(ba),'after':sizes(bb)},'unchanged_A2_files':len([f for f in existing if f.startswith('01_New_Design/kicad_direct/')])-1,'units':'grid=1.27 mm on schematic, not PCB; bounds include power/GND/flag symbols but not text/graphics extents'}
(H/'drawing_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2));assert result['all_pass']
