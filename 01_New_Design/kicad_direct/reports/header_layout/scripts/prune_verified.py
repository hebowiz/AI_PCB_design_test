from common import *
# Reversible pruning of this turn's experimental GND route only; one item per trial.
# Every accepted deletion must pass full KiCad DRC with ZERO new violations/unconnected.
ids=['0630119b-c733-41b4-b46f-aac7b2c24947','085e4660-e232-4522-8bd9-e87c912a28f9','0f37eabd-77ea-4466-9e22-42e1ba62e2e3','266dc629-99b5-4be0-a937-3755dc617332','3e493be2-5ffe-4200-8a68-8d5ab01407c4','7f0f47a4-fbd4-4b41-ad08-38d5aa7229f0','80913083-908c-422e-b5b9-d994fba832ea','9e68d7b4-9241-411a-84cb-9f0bfc461352','bf5d7d48-1a36-44bd-adcb-645f9ac08220','d0809065-0eb9-4a89-aeb6-a57f9453d7c7','da0d8af8-298e-428c-842a-4768a06692f9','df181d3a-883a-43ff-bd1f-d2444d61aead','e4ec510f-e711-4090-83a3-923eca6ab0bc','e73178c4-44ec-464d-b45b-6e235380b289','f0a93615-2a0d-49d7-bce2-a9156f316519','05314228-d474-4a40-bae9-b3ee41ab823c','09db138a-cee6-4aa2-a923-12ab56471009','36929517-0e2c-4d84-9547-5e38ec8865d8','f06e74c5-c933-4f14-afb0-4712c2239c0d','2b21424d-7c37-4157-a098-f92beeb3be73','2e85f8ee-b0e0-4d37-a089-6148007b1911','3b8d364c-bd2d-4a95-8658-e73d4cdf02ad','670129ce-2154-4120-9743-067aab2325e0','694b86af-7aec-4f61-96ea-dcac6e8235cd','98dcde5e-2534-48d2-aee3-90f10e223ec7','bd9e7ff3-ed3e-4a53-ae51-c3efac81fed9','bf8efacd-3f81-4e01-aa24-59ec8ba85217','e004910a-518f-4bc3-bef3-63ff94f95f9f','e96e617c-1fc8-479e-9d9f-bd61ad388395']
base=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));assert not set(ids)&{uid(t) for t in base.GetTracks()}
log=[]
for id in ids:
 t=next((t for t in b.GetTracks() if uid(t)==id),None)
 if t is None:continue
 row=record(t);remove(t);save()
 p=OUT/'checks/prune_trial.json';subprocess.run([str(CLI),'pcb','drc','--format','json','--severity-all','-o',str(p),str(BOARD)],stdout=subprocess.DEVNULL,check=True);r=json.loads(p.read_text())
 ok=not r['violations'] and not r['unconnected_items']
 if not ok:b.Add(t);save()
 log.append({'item':row,'accepted':ok,'violations':len(r['violations']),'unconnected':len(r['unconnected_items'])});print('prune',id,ok,flush=True)
(OUT/'ground_prune_validation.json').write_text(json.dumps(log,indent=2));drc('pruned')
