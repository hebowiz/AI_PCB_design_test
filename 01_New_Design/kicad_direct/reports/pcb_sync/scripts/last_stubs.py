from pathlib import Path
import pcbnew as p,json,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'reports/pcb_sync';path=ROOT/'a2_usb_uart.kicad_pcb'
plan=json.loads((OUT/'stub_cleanup_plan.json').read_text());assert hashlib.sha256(path.read_bytes()).hexdigest()==plan['board_sha256']
# Reviewed complete dead-end branches: former U6 control and former C12 VPLL.
ids='''1b4d24d3-827f-4f3a-b2f2-a42c4e1d5e28 26e4b736-3633-4507-a27a-0a94ca1a6a13 2ba74b79-8f64-4837-83c5-e04647143598 2f46371b-2d1b-438a-bd62-c10955e8fadc 9301c21d-7db6-4881-a674-d14b229f284a a83ac6fa-5d2c-4b24-b666-3e79b2089290 cf207f8b-346c-4b0a-a146-e809019bdfcb d128ca7f-91ad-43a9-9b23-48c0e918c4a2 ed80a14c-db50-4731-ac98-14fb11f204b0 f0a0797d-4e12-4d99-98c5-2af94f343f54 23df38e1-c3bb-4a32-b4e0-eb566c623714 319d625d-e6e4-4b13-ad6e-f55aa68f3b64 7b95f28d-62a4-4972-a394-2de8100ed322 a95c14b2-081e-4c24-8070-88c10f2a89ee dff2ed03-62de-46fd-9098-d88a80c80c43 e6a5cfb9-3e58-45fb-bce5-240b104674c8 fd20453f-962d-4e49-8fc7-032d300cb9ab'''.split()
assert set(ids)=={r['uuid'] for r in plan['proposed']}
b=p.LoadBoard(str(path));ts={t.m_Uuid.AsString():t for t in b.GetTracks()}
for uid in ids:assert ts[uid].GetNetname() in ['/PWR_EN','VPLL']
(OUT/'before/before_last_stubs.kicad_pcb').write_bytes(path.read_bytes())
for uid in ids:b.Remove(ts[uid])
p.SaveBoard(str(path),b);print('Removed 17 reviewed obsolete-branch segments')
