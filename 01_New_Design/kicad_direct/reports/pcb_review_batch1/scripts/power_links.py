from local_tools import *
pairs=[('C23',1,'U1',40),('C1',1,'C23',1),('C5',1,'U1',39),('C2',1,'C5',1),('C3',1,'U1',12),('C4',1,'U1',24),('C6',1,'U1',46),('C7',1,'U1',37),('C8',1,'U1',38),('C9',1,'U1',3),('C10',1,'U1',8),('FB1',2,'C9',1),('FB2',2,'C10',1),('C11',1,'C9',1),('C12',1,'C10',1),('C15',1,'U5',8),('C16',1,'U2',1),('C16',1,'U2',2),('C17',1,'U2',16),('C18',1,'U4',1),('C19',1,'U4',5)]
results=[]
for ar,an,br,bn in pairs:
 a,c=pad(ar,an),pad(br,bn);assert a.GetNetCode()==c.GetNetCode();ok,vis=route(endpoint(a),endpoint(c),a.GetNetCode(),allow_via=False)
 if not ok:ok,vis=route(endpoint(a),endpoint(c),a.GetNetCode())
 result={'from':f'{ar}.{an}','to':f'{br}.{bn}','success':ok,'visited':vis};print(result,flush=True);results.append(result);save();refresh()
(OUT/'power_links.json').write_text(json.dumps(results,indent=2));drc('power_links')
