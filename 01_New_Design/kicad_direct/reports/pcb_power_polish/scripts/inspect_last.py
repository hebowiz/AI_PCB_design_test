from geom import *
ids={'bde42f4f-0c6f-4f9a-bc44-aca718144da3','e3f791c2-b5df-4a51-af9c-9ebb3c7477d5','066b8d3a-8faa-4f2e-9d9a-56a92ae2da59','adfd8ec2-3a67-4e77-89e7-b5f277acd327'}
for t in b.GetTracks():
 if uid(t) in ids or (t.GetNetname()=='/CTS_N' and t.GetLayer()==0 and min(xy(t.GetStart())[1],xy(t.GetEnd())[1])<131.1):print(record(t))
