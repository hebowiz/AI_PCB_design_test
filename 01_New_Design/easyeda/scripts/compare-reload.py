"""Compare saved/reopened CAD geometry and netlists, independent of session IDs."""
import json,hashlib,re,math
from pathlib import Path
b=Path(__file__).resolve().parents[1]
a=json.loads((b/'reports/before-reload.json').read_text(encoding='utf-8-sig'))['value'];z=json.loads((b/'reports/after-reload.json').read_text(encoding='utf-8-sig'))['value']
def stable(x):
    if isinstance(x,list):
        r=[stable(v) for v in x]
        if all(isinstance(v,dict) for v in r):r.sort(key=lambda d:d.get('primitiveId',d.get('id',d.get('ref',''))))
        return r
    if isinstance(x,dict):return {k:stable(v) for k,v in sorted(x.items()) if k not in ['async']}
    return x
def sha(x):return hashlib.sha256(json.dumps(stable(x),sort_keys=True,separators=(',',':')).encode()).hexdigest()
def netlist(s):
    pins={};parts={}
    for block in re.findall(r'^\(\s*\n(.*?)^\)\s*$',s,re.M|re.S):
        lines=block.strip().splitlines()
        for line in lines[1:]:pins[line.split()[0]]=lines[0].strip()
    for block in re.findall(r'^\[\s*\n(.*?)^\]\s*$',s,re.M|re.S):
        lines=block.rstrip('\r\n').splitlines();d=dict(zip(lines[::2],lines[1::2]));ref=d.get('DESIGNATOR')
        if ref:parts[ref]={k:d.get(k) for k in ['FOOTPRINT','PARTTYPE','Manufacturer Part','Manufacturer','Supplier Part','Value','Device']}
    return {'pins':pins,'parts':parts}
def compare(x,y,path='',tol=.00011,stack=False):
    if isinstance(x,dict) and isinstance(y,dict):
        out=[]
        for k in x.keys()|y.keys():out+=compare(x.get(k,'MISSING'),y.get(k,'MISSING'),path+'/'+k,tol,stack)
        return out
    if isinstance(x,list) and isinstance(y,list):
        if len(x)!=len(y):return [(path,'length',len(x),len(y))]
        return [v for i,(c,d) in enumerate(zip(x,y)) for v in compare(c,d,path+'/'+str(i),tol,stack)]
    if stack and path.rsplit('/',1)[-1] in ['lossTangent','permittivity'] and x in [None,0] and y in [None,0]:return []
    if isinstance(x,(int,float)) and not isinstance(x,bool) and isinstance(y,(int,float)) and not isinstance(y,bool):
        delta=abs(x-y)
        if path.lower().endswith('rotation'):delta=abs((x-y+180)%360-180)
        return [] if delta<=tol else [(path,x,y,delta)]
    return [] if x==y else [(path,x,y)]
fields=['components','lines','vias','pours','stackup','rules','schNetlist','pcbNetlist'];checks={}
for f in fields:
    x,y=(netlist(a[f]),netlist(z[f])) if f.endswith('Netlist') else (stable(a[f]),stable(z[f]))
    tolerance=.001 if f=='stackup' else 1e-9 if f=='rules' else .00011
    differences=compare(x,y,tol=tolerance,stack=f=='stackup')
    checks[f]={'sameWithinDocumentedNormalization':not differences,'rawIdentical':sha(a[f])==sha(z[f]),'beforeSha256':sha(a[f]),'afterSha256':sha(z[f]),'differences':differences}
r={'passed':all(v['sameWithinDocumentedNormalization'] for v in checks.values()) and a['erc'] and z['erc'] and a['drc'] and z['drc'] and z['ratlines']['total']==0,'normalization':{'geometryToleranceMil':.00011,'stackupToleranceMil':.001,'rotation':'modulo 360','unsetMaterialProperties':'null and 0 treated as unset','netlists':'compare all pin/net assignments and keyed part identity; ignore ordering and unrelated metadata'},'checks':checks,'ercAfter':z['erc'],'drcAfter':z['drc'],'ratlinesAfter':z['ratlines']['total'],'pcbComponents':len(z['components']),'allTop':all(c['layer']==1 for c in z['components']),'tracks':len(z['lines']),'vias':len(z['vias']),'pours':len(z['pours'])}
(b/'reports/save-reload-verification.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 1)
