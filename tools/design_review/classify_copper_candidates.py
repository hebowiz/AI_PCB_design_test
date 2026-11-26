"""Read-only, conservative candidate triage with per-item images and network plans.
No Load/Save round trip or zone refill. Proposed exceptions require human review.
"""
import argparse,base64,collections,hashlib,html,io,json,math,sys
from pathlib import Path
ap=argparse.ArgumentParser(description=__doc__)
for n in ('board','metrics','out','packages'):ap.add_argument('--'+n,type=Path,required=True)
ap.add_argument('--assessments',type=Path)
a=ap.parse_args();sys.path.insert(0,str(a.packages))
import pcbnew as k
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union
from PIL import Image,ImageDraw,ImageFont
start=hashlib.sha256(a.board.read_bytes()).hexdigest();m=json.loads(a.metrics.read_text(encoding='utf-8'));assert start==m['board_sha256']
a.out.mkdir(parents=True,exist_ok=True);b=k.LoadBoard(str(a.board));keep=list(b.GetTracks());L={k.F_Cu:'F.Cu',k.B_Cu:'B.Cu'}
xy=lambda q:(round(k.ToMM(q.x),6),round(k.ToMM(q.y),6))
def parts(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return [p for c in getattr(g,'geoms',[]) for p in parts(c)]
def poly(s):
 def ring(r):return [xy(r.CPoint(i)) for i in range(r.PointCount())]
 return unary_union([Polygon(ring(s.COutline(i)),[ring(s.CHole(i,j)) for j in range(s.HoleCount(i))]) for i in range(s.OutlineCount())])
tracks=[];pads=[];vias=[];zones=[]
for t in keep:
 r={'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'at':xy(t.GetStart())}
 if isinstance(t,k.PCB_VIA):
  r.update(width=k.ToMM(t.GetWidth(k.F_Cu)),hole=k.ToMM(t.GetDrillValue()));r['g']=Point(r['at']).buffer(r['width']/2);vias.append(r)
 else:
  if isinstance(t,k.PCB_ARC):raise ValueError('Arc unsupported')
  r.update(end=xy(t.GetEnd()),layer=L[t.GetLayer()],width=k.ToMM(t.GetWidth()));r['line']=LineString([r['at'],r['end']]);r['g']=r['line'].buffer(r['width']/2,quad_segs=16);tracks.append(r)
for f in b.GetFootprints():
 for p in f.Pads():
  for l,ln in L.items():
   if not p.IsOnLayer(l):continue
   s=k.SHAPE_POLY_SET();p.TransformShapeToPolygon(s,l,0,k.FromMM(.001),k.ERROR_OUTSIDE)
   pads.append({'pin':f.GetReference()+'.'+p.GetNumber(),'net':p.GetNetname(),'at':xy(p.GetPosition()),'layer':ln,'g':poly(s)})
for z in b.Zones():
 if z.GetIsRuleArea():continue
 for l,ln in L.items():
  if z.IsOnLayer(l):zones.append({'net':z.GetNetname(),'layer':ln,'g':poly(z.GetFilledPolysList(l))})
# Reconstruct the exact morphology regions used by the original detector.
regions={};idx=0
for ln in L.values():
 zone=unary_union([z['g'] for z in zones if z['net']=='GND' and z['layer']==ln]);opened=zone.buffer(-.5,quad_segs=16).buffer(.5,quad_segs=16).intersection(zone)
 for p in parts(zone.difference(opened.buffer(.01))):
  if p.area<.02:continue
  idx+=1;regions[idx]=p
assert idx==len(m['narrow_ground'])
rawregions=list(regions.values());regions={r['id']:min(rawregions,key=lambda p:sum(abs(u-v) for u,v in zip(p.bounds,r['bounds']))) for r in m['narrow_ground']}
T={t['uuid']:t for t in tracks};rows=[]
def near(pt):return sorted(pads,key=lambda p:Point(pt).distance(p['g']))[:4]
def row(kind,i,r):
 x={'id':kind+f'{i:03}','kind':kind,'net':r.get('net','GND'),'layer':r['layer'],'at':r['at'],'source':r,'class':'要修正','exception_approved':False,'evidence':{},'near_pins':[p['pin'] for p in near(r['at'])]};rows.append(x);return x
def plan(x):
 net=x['net'];pins=sorted({p['pin'] for p in pads if p['net']==net});x['net_terminals']=pins
 x['recommended']='ネット全体の端子間経路を見直し、短辺中央の直線引出しから長い45°区間へ接続する。既存の短い面取り線分は固定しない。'
 x['relaxation']='当該ネットの経路・ビア位置の固定を解除。交差する隣接ネットは別途一覧の影響範囲で局所再配線を検討。'
 if net in ('USB5V','/USB5V_SW','USB5V_OUT','+3V3','VIO','VIO_OUT','VPHY','VPLL','VCORE_1V8','VCCA_1V8'):
  x['recommended']='電源元・大容量C・小容量C・入力ピンの経路を単位として再配線し、分岐を容量端子かビアへ集約する。GND帰路も同時に確保する。'
  x['relaxation']='同一電源系の配線固定を解除。容量と周辺抵抗の局所移動を候補に含め、電源順序・IC近接・GND帰路を再検証する。'
 if net.startswith('/USB_D') or net.startswith('/XTAL'):
  x['recommended']='ペア全体の端点と引出しを一緒に見直す。ESD/負荷容量の分岐を部品端子へ収め、差動/発振経路と直下GNDを再検証する。'
  x['relaxation']='USB/水晶の線分UUID・経路の完全固定を緩和する必要がある。J1・U1位置、インピーダンス条件、ペア性、直下GNDは維持する。'
 if net=='GND':x['recommended']='信号・電源の再配線後にGNDを再評価し、必要な帰路の拡幅または反対層への補強を行う。';x['relaxation']='GNDゾーン輪郭とステッチ位置の固定を解除。接続先・参照面・サーマルを保護する。'
for i,r in enumerate([p for p in m['pseudo_right_angles'] if p['within_proposed_limit']],1):
 x=row('P',i,r);plan(x);x['reason']=f"同方向45°が2回続き、中間{r['middle_length_mm']:.3f}mm、線幅比{r['length_width_ratio']:.2f}。小さな角だけの置換ではなく端子間経路を作り直す。"
 x['evidence']={'middle_length_mm':r['middle_length_mm'],'width_mm':r['width_mm'],'uuids':r['uuids']}
for i,r in enumerate([p for p in m['branches'] if not p['at_pad_or_via']],1):
 x=row('B',i,r);plan(x);pt=Point(r['at']);touch=[p for p in pads if p['layer']==x['layer'] and p['net']==x['net'] and p['g'].distance(pt)<.005]
 x['reason']=f"端子外の次数{r['degree']}分岐。多端子ネットであっても、この位置で途中分岐する必要は未立証。端子/ビア起点の木構造へ変更する。"
 if touch:x.update({'class':'誤検出','reason':'分岐点は実際の同一ネットパッド銅箔内。端子外という分類は誤り。形状の鋭い切込みはN項目で別評価。','recommended':'途中分岐件数から除外し、パッド接続形状の評価を残す。'})
 elif x['net']=='GND':x.update({'class':'合理的な例外','reason':'GNDの並列帰路に属する接続。分岐の存在だけを減らすと帰路を損なうため保持を提案。鋭い空隙は別評価し、例外承認は未取得。'})
 x['evidence']={'touching_pads':[p['pin'] for p in touch],'uuids':r['uuids']}
 def pointparts(geom):
  if geom.is_empty:return []
  if geom.geom_type=='Point':return [geom]
  return [p for g in getattr(geom,'geoms',[]) for p in pointparts(g)]
 netline=unary_union([t['line'] for t in tracks if t['net']==x['net'] and t['layer']==x['layer']]);counts={}
 for radius in [.01,.05,.1,.25]:
  angles=[]
  for q in pointparts(netline.intersection(pt.buffer(radius,quad_segs=64).boundary)):
   angle=math.degrees(math.atan2(q.y-pt.y,q.x-pt.x))
   if not any(min(abs(angle-v),360-abs(angle-v))<2 for v in angles):angles.append(angle)
  counts[str(radius)]={'count':len(angles),'angles_deg':sorted(round(v,3) for v in angles)}
 x['evidence']['radial_intersections']=counts
# Ground: do not infer "useless" from absence of a pad in the residual alone.
for r in m['narrow_ground']:
 x=row('G',r['id'],r);plan(x);p=regions[r['id']];assert abs(p.area-r['area_mm2'])<1e-5
 contacts=[t for t in tracks if t['net']=='GND' and t['layer']==r['layer'] and t['g'].intersects(p)]
 terminals=[q for q in pads if q['net']=='GND' and q['layer']==r['layer'] and q['g'].distance(p)<.02]
 vs=[v for v in vias if v['g'].distance(p)<.02 and v['net']=='GND']
 thermalcover=unary_union([q['g'].buffer(.4) for q in terminals]+[v['g'].buffer(.4) for v in vs])
 ratio=p.intersection(thermalcover).area/p.area if not thermalcover.is_empty else 0
 fullzone=unary_union([z['g'] for z in zones if z['net']=='GND' and z['layer']==r['layer']])
 widths=r['section_width_mm'];small=max(p.bounds[2]-p.bounds[0],p.bounds[3]-p.bounds[1])<.7
 # Stronger corner test: compact residue, both through-sections >=1mm, no GND terminal or route.
 corner=small and all(v is not None and v>=1 for v in widths.values()) and not contacts and not terminals and not vs
 x['evidence']={'area_mm2':r['area_mm2'],'section_width_mm':widths,'ground_track_contacts':[t['uuid'] for t in contacts],'terminal_contacts':[q['pin'] for q in terminals],'via_contacts':[v['uuid'] for v in vs],'thermal_neighborhood_fraction':round(ratio,4),'morphology_polygon':list(p.exterior.coords),'core_contact_regions':r['core_contact_regions']}
 if ratio>.98 and p.area<.45 and (terminals or vs):
  x['class']='合理的な例外';x['reason']='候補の98%以上が接続GND端子/ビアの周囲0.4mm内にあり、面積0.45mm²未満。局所サーマル/パッド接続の細線として保持を提案。1mm幅の幹線とは区別し、例外承認待ち。';x['recommended']='サーマル接続を維持。端子ごとの帰路の連続性、スポーク本数と電流・実装条件を修正後に再確認する。'
 elif corner:
  x['class']='誤検出';x['reason']='0.7mm未満の小領域で、候補点を通る水平・垂直の実銅箔断面はいずれも1mm以上。端子/配線接触なし。開操作が境界を丸めた残差を細線として抽出している。';x['recommended']='本候補を幅不足から除外。周辺の独立した細いネックや空隙は別候補で評価する。'
 elif contacts or terminals or vs or r['core_contact_regions']>=2:
  x['reason']='必要な接続/帰路、または複数の太い領域との接点を含む。切除を優先せず、1mm未満のネックを解消する再配線を検討する。'
  x['recommended']='周囲の信号・電源を移してGND幹線を1mm以上へ拡幅。拡幅不能なら両面の接続先を確認したGNDビア補強を提案し、幅不足の例外承認を別途受ける。'
 else:
  x['reason']='候補内に直接GND端子・ビア・GND配線との接触がない。帰路不要と即断せず、参照信号との重なりを確認して不要な突起を除去する対象とする。'
  x['recommended']='信号直下の参照面でなければゾーン輪郭で突起を除去。参照面なら関連信号を含めて経路を移し、太いGND面へ統合する。端子有無だけで削除しない。'
 # exact nearby opposite-side signal references, not a claim of required return current.
 opp='B.Cu' if r['layer']=='F.Cu' else 'F.Cu'
 refs=[t for t in tracks if t['layer']==opp and t['net']!='GND' and t['g'].intersects(p)]
 x['evidence']['opposite_tracks']=[{'net':t['net'],'uuid':t['uuid']} for t in refs]
 if refs and x['class']=='要修正':x['reason']+=' 反対面配線の直下と重なるため、無条件切除は禁止。'
# Evaluate reentrant voids explicitly. All notches retained as repair candidates unless proven sampling artifacts by manual assessment.
for i,r in enumerate([q for q in m['acute_copper'] if q['scope']=='saved_copper'],1):
 x=row('N',i,r);plan(x);x['reason']=f"銅箔内角{r['copper_interior_deg']:.2f}°、空隙側{360-r['copper_interior_deg']:.2f}°。凸角0件でも、この切込みは未解消。"
 x['evidence']={'void_angle_deg':round(360-r['copper_interior_deg'],3),'incident_edge_lengths_mm':r['edge_lengths_mm'],'source_scope':r['scope']}
 x['recommended']='関連ネットの分岐・引出しを作り直して空隙角を90°以上へ。GNDでは隣接配線との間の突起を切除するか帰路幅を確保し、切込みを残さない。'
assessments=json.loads(a.assessments.read_text(encoding='utf-8')) if a.assessments else {'overrides':{}}
if a.assessments:assert assessments['source_sha256']==start
for x in rows:
 override=assessments['overrides'].get(x['id'],{})
 x['evidence'].update(override.get('evidence_add',{}))
 x.update({key:value for key,value in override.items() if key!='evidence_add'})
# Loop and overlap of VIO are separate findings, linked to the historical R-0030 review.
for i,q in enumerate([q for q in m['route_geometry_details']['cycles'] if q['net']=='VIO'],1):
 pts=q['points'];r={'net':'VIO','layer':'F.Cu','at':[sum(p[0] for p in pts)/len(pts),sum(p[1] for p in pts)/len(pts)],'bounds':[min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)],'uuids':q['uuids']}
 x=row('V',i,r);plan(x);x['reason']='R-0030承認版では存在せず、J2/J3配置変更後から現れるVIO並列閉路。電流・帰路上の必要性は記録されておらず、木構造への再配線対象。';x['evidence']=q;x['recommended']='U4.5→C19.1→C17.1→U2.16を幹線とし、SW3/R7/R11/R12への分岐を端子起点で整理。閉路の一辺だけの撤去で済ませず、C19バイパス経路と重複を一緒に解消する。'
for i,q in enumerate([q for q in m['route_geometry_details']['duplicate_overlap'] if q['net']=='VIO'],1):
 bd=q['bounds'];r={'net':'VIO','layer':'F.Cu','at':[(bd[0]+bd[2])/2,(bd[1]+bd[3])/2],'bounds':bd,'uuids':q['uuids']}
 x=row('D',i,r);plan(x);x['reason']='同一直線上のVIO配線が0.25mm重なる。独立した電流経路を増やさず、幾何学的な重複である。';x['evidence']=q;x['recommended']='VIO全体の木構造化と同時に重複線分を統合。パッド接続・電源容量の順序を再検証する。'
# Plans include exact network members and nearby non-net obstacles, never automatic authorization.
for x in rows:
 if x['class']=='誤検出':x['relaxation']='本候補単独の保護緩和は不要。別項目による同一ネットの再配線時に追従する。'
 elif x['class']=='合理的な例外':x['relaxation']='本候補の削除・移動を必須としない。例外の採否を確認し、周辺再配線後に機能・帰路を再評価する。'
 x['near_pins']=[q['pin'] for q in near(x['at'])]
 vicinity=Point(x['at']).buffer(1.0)
 x['affected_adjacent_nets']=sorted({t['net'] for t in tracks if t['layer']==x['layer'] and t['net']!=x['net'] and t['g'].intersects(vicinity)})
 x['related_ids']=[q['id'] for q in rows if q is not x and q['layer']==x['layer'] and math.dist(q['at'],x['at'])<.65]
 x['image']='inspection.html#'+x['id']
# Images use saved copper, highlighted source segments and morphology, no PCB changes.
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13);large=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
def render(x,w=480):
 r=x['source'];pt=x['at'];bounds=r.get('bounds')
 if bounds:
  cx=(bounds[0]+bounds[2])/2;cy=(bounds[1]+bounds[3])/2;span=max(2.6,bounds[2]-bounds[0]+.9,(bounds[3]-bounds[1]+.9)*1.4)
 else:cx,cy=pt;span=3.4
 h=round(w*.75);scale=w/span;bd=(cx-span/2,cy-span*.375,cx+span/2,cy+span*.375);clip=box(*bd)
 im=Image.new('RGB',(w,h+47),(20,25,31));d=ImageDraw.Draw(im);cv=lambda q:((q[0]-bd[0])*scale,47+(q[1]-bd[1])*scale)
 def draw(g,col,outline=False):
  for p in parts(g.intersection(clip)):
   pp=[cv(q) for q in p.exterior.coords]
   if outline:d.line(pp,fill=col,width=2)
   else:
    d.polygon(pp,fill=col)
    for hole in p.interiors:d.polygon([cv(q) for q in hole.coords],fill=(20,25,31))
 for z in zones:
  if z['layer']==x['layer']:draw(z['g'],(72,48,47) if x['layer']=='F.Cu' else (35,47,76))
 for t in tracks:
  if t['layer']==x['layer']:draw(t['g'],(246,171,76) if t['uuid'] in r.get('uuids',[]) else ((224,95,82) if x['layer']=='F.Cu' else (83,129,234)))
 for p in pads:
  if p['layer']==x['layer']:draw(p['g'],(175,151,92))
 for v in vias:draw(v['g'],(199,174,100));draw(Point(v['at']).buffer(v['hole']/2),(20,25,31))
 if x['kind']=='G':draw(regions[r['id']],(255,70,223),True)
 for p in pads:
  if p['layer']==x['layer'] and clip.contains(Point(p['at'])):d.text(cv(p['at']),p['pin'],font=font,anchor='mm',fill='white',stroke_width=1,stroke_fill='black')
 q=cv(pt);d.ellipse((q[0]-7,q[1]-7,q[0]+7,q[1]+7),outline='cyan',width=2)
 d.rectangle((0,0,w,47),fill=(9,14,19));d.text((8,4),x['id']+' '+x['net']+' '+x['layer'],font=large,fill='white');d.text((8,25),f'X {pt[0]:.4f} Y {pt[1]:.4f} mm | span {span:.2f} mm',font=font,fill='white')
 return im
summary={kind:dict(collections.Counter(x['class'] for x in rows if x['kind']==kind)) for kind in ['P','B','G','N','V','D']}
plans=[]
for net in sorted({x['net'] for x in rows if x['class']=='要修正'}):
 rr=[x for x in rows if x['net']==net and x['class']=='要修正'];ts=[t for t in tracks if t['net']==net]
 plans.append({'net':net,'candidate_ids':[x['id'] for x in rr],'pins':sorted({p['pin'] for p in pads if p['net']==net}),'track_count':len(ts),'track_length_mm':round(sum(t['line'].length for t in ts),5),'track_uuids':[t['uuid'] for t in ts],'via_uuids':[v['uuid'] for v in vias if v['net']==net],'adjacent_nets':sorted({n for x in rr for n in x['affected_adjacent_nets']}),'recommended':rr[0]['recommended'],'relaxation':rr[0]['relaxation']})
result={'source_sha256':start,'counts':summary,'classification_status':'Analyst proposal; rational exceptions are not human-approved. Ambiguous candidates conservatively remain repair-required.','records':rows,'network_plans':plans,'analyst_assessments':assessments}
(a.out/'classification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
# Single self-contained searchable dossier avoids a file per finding.
head='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>A-2 候補分類</title><style>body{font:15px system-ui;background:#f5f6f8;color:#17202a;margin:20px}header{position:sticky;top:0;background:#fff;padding:12px;z-index:1}article{background:white;border:1px solid #ccd3db;border-radius:6px;padding:14px;margin:12px 0;display:grid;grid-template-columns:480px 1fr;gap:18px}img{width:480px;max-width:100%}h2{margin:0 0 10px}p{line-height:1.6}input,select{padding:8px;margin:4px}code{overflow-wrap:anywhere}a{color:#075ca8}</style><header><h1>A-2 配線・GND候補の再分類</h1><p>PCB未変更。黄線＝対象線分、紫輪郭＝GND候補、青丸＝座標。例外は技術提案でありユーザー承認待ち。類似箇所は重複計数を含む。</p><input id="q" placeholder="ID / ネット / 部品 / 座標"><select id="c"><option value="">全分類</option><option>要修正</option><option>合理的な例外</option><option>誤検出</option></select><span id="count"></span></header>'''
out=[head];esc=lambda v:html.escape(str(v))
for x in rows:
 im=render(x);buf=io.BytesIO();im.save(buf,format='PNG');encoded=base64.b64encode(buf.getvalue()).decode()
 text=' '.join([x['id'],x['net'],x['class'],str(x['at']),' '.join(x['near_pins']),x['reason']])
 out.append(f'<article id="{x["id"]}" data-cat="{x["class"]}" data-search="{esc(text)}"><img loading="lazy" alt="{esc(text)}" src="data:image/png;base64,{encoded}"><div><h2>{x["id"]}　{esc(x["net"])}　{x["class"]}</h2><p>{x["layer"]} / {esc(x["at"])} mm<br>近傍 {esc(", ".join(x["near_pins"]))}</p><p><b>根拠</b> {esc(x["reason"])}</p><p><b>推奨修正</b> {esc(x["recommended"])}</p><p><b>保護緩和</b> {esc(x["relaxation"])}</p><p>隣接ネット {esc(", ".join(x["affected_adjacent_nets"]))}<br>関連 '+', '.join(f'<a href="#{q}">{q}</a>' for q in x['related_ids'])+'</p><details><summary>座標・UUID・測定根拠</summary><pre>'+esc(json.dumps(x['evidence'],ensure_ascii=False,indent=2))+'</pre></details></div></article>')
out.append('''<script>function filter(){let q=document.getElementById('q').value.toLowerCase(),c=document.getElementById('c').value,n=0;document.querySelectorAll('article').forEach(e=>{let yes=(!c||e.dataset.cat===c)&&e.dataset.search.toLowerCase().includes(q);e.style.display=yes?'grid':'none';if(yes)n++});document.getElementById('count').textContent=n+' 件'}document.getElementById('q').oninput=filter;document.getElementById('c').onchange=filter;filter();</script></html>''')
(a.out/'inspection.html').write_text(''.join(out),encoding='utf-8')
# Contact sheets only in temporary output for analyst visual review.
for kind in ['P','B','G','N','V','D']:
 rr=[x for x in rows if x['kind']==kind]
 for startidx in range(0,len(rr),24):
  batch=rr[startidx:startidx+24];ims=[render(x,320) for x in batch];sheet=Image.new('RGB',(1280,287*math.ceil(len(batch)/4)),(240,240,240))
  for j,im in enumerate(ims):sheet.paste(im,((j%4)*320,(j//4)*287))
  sheet.save(a.out/f'{kind}-{startidx//24+1}.png')
print(json.dumps(summary,ensure_ascii=False));assert start==hashlib.sha256(a.board.read_bytes()).hexdigest()

