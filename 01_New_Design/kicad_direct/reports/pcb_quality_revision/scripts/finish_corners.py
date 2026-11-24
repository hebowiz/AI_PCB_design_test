from common import *
assert BOARD.parent==OUT.resolve()/'candidate'
snapshot=BOARD.read_bytes()
s=(OUT/'scripts/chamfer_corners.py').read_text(encoding='utf-8-sig').replace("'chamfers.json'","'chamfers_final.json'").replace("'chamfer_remaining.json'","'chamfer_remaining_final.json'").replace("drc('chamfers')","result=drc('chamfers_final')")
try:
 exec(compile(s,'chamfer_corners.py','exec'))
 if result['violations'] or result['unconnected_items']:raise RuntimeError('final corner DRC failed')
except:
 if BOARD.read_bytes()!=snapshot:(OUT/'checks/corners_failed.kicad_pcb').write_bytes(BOARD.read_bytes());BOARD.write_bytes(snapshot)
 raise
