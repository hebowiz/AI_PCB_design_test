from pathlib import Path
import pcbnew as p,json,hashlib,math,types,sys
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'reports/pcb_sync';path=ROOT/'a2_usb_uart.kicad_pcb'
plan=json.loads((OUT/'stub_cleanup_plan.json').read_text());assert hashlib.sha256(path.read_bytes()).hexdigest()==plan['board_sha256']
b=p.LoadBoard(str(path));ts={t.m_Uuid.AsString():t for t in b.GetTracks()}
# Explicit inspected branches: disconnected former VREGIN segment, obsolete U3/U6,
# moved C1/C12, old D1 junction and SW2 output stub. Not a DRC-category filter.
selected='''a1aace80-643c-45c5-b54e-a6b35fc06e97 b37070a7-b1db-4724-9a53-57a1aab47fa0 d2ff89f5-78a0-472d-a422-1559c6b44559 f5f9da72-0384-4435-b2f8-65aea685ed8e 3237e3f4-3209-4e60-a239-a744b2443625 3f1e0e42-2e52-435d-aa27-7809733cc5ff 748f3234-86db-475e-8d7d-cb40def78916 759a3487-c7ca-4960-90eb-8f4a62890ed5 c390b435-e790-4e92-ae91-b683ca67a76b cb399d4b-2031-4171-9859-8b7361f386e6 00770770-51ce-4e7d-8fbb-3ea8551c4287 d4a6b61c-bc8d-47d2-bf98-16c74ea81d1f 384167fc-4c64-4481-a620-791058fac6eb 2dc5f80d-ba14-463d-a14a-91b4fed4886c 3e322b20-1758-4e62-b842-1dfbb810a07f be9bec84-234e-4e7c-b731-19320b107a15 cb65c01f-44c3-4152-bb5d-96e98e48fcf2 d9def447-5915-4ca0-b7aa-933193c1c43d dbeae2ca-f1c9-450a-a576-d85614d510f8 e8e29465-0538-4a0f-b4ed-c38066eec21f f30b0c0b-b55e-47bc-8f18-52fa94be09e6 a1cbaef5-64fd-4e4d-b651-d3788bf17888 b05b8f74-ffc0-4e43-be19-6095ec236ef0 6fe140fd-799b-4865-b7cf-859da84c43c3 d3dd2efc-b8be-466b-880f-bab18e2b19c8'''.split()
assert len(selected)==25
(OUT/'before/routed_before_cleanup.kicad_pcb').write_bytes(path.read_bytes())
for uid in selected:b.Remove(ts[uid])
# Add one GND stitch in the isolated zone beside the new D5.
source=(ROOT/'scripts/route.py').read_text(encoding='utf8').split("if __name__ == '__main__':")[0].replace('from design import ROOT','')
import __main__
__main__.ROUTER_BOARD=b;sys.argv=['local','--continue-existing'];r=types.ModuleType('r');r.ROOT=ROOT
exec(compile(source,str(ROOT/'scripts/route.py'),'exec'),r.__dict__)
gnd=b.FindNet('GND').GetNetCode();mask,vm=r.obstacles(gnd)
fz=next(z for z in b.Zones() if z.GetLayer()==p.F_Cu);island=fz.GetFilledPolysList(p.F_Cu).COutline(21)
candidates=[]
for ix in range(2230,2258):
 for iy in range(2160,2192):
  x,y=ix*.05,iy*.05;pos=p.VECTOR2I(p.FromMM(x),p.FromMM(y));n=r.node(x-100,y-100)
  if island.PointInside(pos) and not vm[n]:candidates.append((math.dist((x,y),(112.25,108.7)),x,y))
assert candidates,'No safe ground stitch position'
_,x,y=min(candidates);r.via(x-100,y-100,gnd)
p.SaveBoard(str(path),b)
(OUT/'local_cleanup.json').write_text(json.dumps({'removed_uuids':selected,'ground_stitch':[x,y]},indent=2),encoding='utf8')
print('25 inspected obsolete objects removed; GND stitch',x,y)
