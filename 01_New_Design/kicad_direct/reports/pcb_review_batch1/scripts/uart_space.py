from common import *
t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()=='a1cbdaa5-06e7-4be5-acf4-b2956d253992');remove(t);line([(109.4,124),(110,124.6),(110,133.3),(109.4,133.9)],'USB5V',w=.15)
a=pad('U2',8);pt=xy(a.GetPosition());new=(109.175,130.625);tr(pt,new,a.GetNetname(),w=.15);fan=json.loads((OUT/'fanouts.json').read_text());fan['U2.8']=new;(OUT/'fanouts.json').write_text(json.dumps(fan,indent=2));save();drc('uart_space')
