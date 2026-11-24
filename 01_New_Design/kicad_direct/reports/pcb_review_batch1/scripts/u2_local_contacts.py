from common import *
# Only the four identified grazing pad contacts and two adjacent staircase sections.
rx_ids=['04677714-955e-4538-bb48-fb52297616b5','18fc7aa4-4ba6-430a-ba4c-a47b10d578be','1b890870-221b-4045-9982-2968f98196cd','216be008-45c6-456d-a31b-1790f2dfc137','21f53ab7-6f13-434d-8f48-a7d903d5af06','54d605be-00d7-4d4c-b0d6-a4720ca1aa05','566dd72c-51be-4861-be8d-7a782e65b883','5ad3a1e7-9577-4b41-bf55-b45b5b582639','79caff8e-c958-469d-97c5-d7168f4d9044','7d983092-f8e5-41c0-9dde-aebf7c579360','9b4c1ee9-8383-43f8-b305-f01682f52283','9cabd20e-cdfd-4205-96e7-79e5d96be8f1','d89b9a6d-03d7-455f-9c02-6c4188a57995','f1fd7df4-9695-46a2-b629-7d9c88bad279']
rts_ids=['098f022c-548d-4f71-b2ac-de277afd7e33','ee10d401-ce8b-42e3-a251-7a8992a547aa','644530fa-ced1-414f-80cc-6ac74c1ff3e6','1ee53a79-3eb9-4500-b9ab-349a849a7cd1']
fixes=[('U2.6',rx_ids,[(106.55,128.6),(106.75,128.8),(106.75,129.575),(107.15,129.975),(108.1375,129.975)]),('U2.12',rts_ids,[(110.8,130.25),(111.975,130.25),(112.9,129.325),(113.8625,129.325)]),('U2.4',['e938ff80-93e0-41b3-bafa-221f0462448e'],[(109.0,128.449999),(109.225001,128.675),(108.1375,128.675)]),('U2.1',['ce8acb26-f10c-43c5-a1bd-f850cca96750'],[(107.75,126.1),(107.25,126.6),(106.38,126.6)])]
idx={t.m_Uuid.AsString():t for t in b.GetTracks()};plan=[]
for pin,ids,pts in fixes:
 assert all(uid in idx for uid in ids);net=idx[ids[0]].GetNetname();assert all(idx[uid].GetNetname()==net for uid in ids)
 plan.append({'pin':pin,'net':net,'replace':[{'uuid':uid,'a':xy(idx[uid].GetStart()),'b':xy(idx[uid].GetEnd())} for uid in ids],'new_polyline':pts})
(OUT/'u2_local_contact_plan.json').write_text(json.dumps(plan,indent=2));(OUT/'before_u2_contact_edit.kicad_pcb').write_bytes((ROOT/'a2_usb_uart.kicad_pcb').read_bytes())
for q in plan:
 for old in q['replace']:remove(idx[old['uuid']])
 line(q['new_polyline'],q['net'],w=.15)
# The duplicated, disconnected enable tail is explicitly identified by the latest DRC.
remove(idx['ee263178-0a8d-474b-9c4a-80dac05a393e'])
d=drc('u2_local_contacts');print('DRC',len(d['violations']),len(d['unconnected_items']))
