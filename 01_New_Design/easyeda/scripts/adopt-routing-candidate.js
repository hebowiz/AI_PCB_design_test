// CANDIDATE is injected from the saved public getAutoJobLog result by the runner.
const mm=v=>v/.0254, protectedNets=new Set(['USB_D_N','USB_D_P']);
await eda.dmt_EditorControl.openDocument('6ee5c30d1c816c19');
const existing=await eda.pcb_PrimitiveLine.getAll();
if(existing.some(l=>!protectedNets.has(l.getState_Net())))throw Error('Other routes already exist; do not duplicate');
const before=existing.map(l=>l.getState_PrimitiveId());
const lines=[],vias=[];
for(const t of CANDIDATE.traces){if(protectedNets.has(t.net))continue;
 if(![1,2].includes(t.layer)||!(t.width>=.127))throw Error('Invalid trace');
 for(let i=1;i<t.path.length;i++){const a=t.path[i-1],b=t.path[i];if(Math.hypot(a[0]-b[0],a[1]-b[1])<.00001)continue;
 const l=await eda.pcb_PrimitiveLine.create(t.net,t.layer,mm(a[0]),mm(a[1]),mm(b[0]),mm(b[1]),mm(t.width),false);lines.push(l.getState_PrimitiveId());}
}
for(const v of CANDIDATE.vias){if(protectedNets.has(v.net))continue;const p=v.location,s=v.size;
 const via=await eda.pcb_PrimitiveVia.create(v.net,mm(p[0]),mm(p[1]),mm(s[1]),mm(s[0]),0,null,null,false);vias.push(via.getState_PrimitiveId());
}
await new Promise(r=>setTimeout(r,4000));
const after=new Set((await eda.pcb_PrimitiveLine.getAll()).map(l=>l.getState_PrimitiveId()));
return {source:'Tentative result from official getAutoJobLog; not a completed autorouter job',candidateRatio:CANDIDATE.routabitity,lines,vias,protectedIdsPreserved:before.every(id=>after.has(id)),saved:await eda.pcb_Document.save(),drc:await eda.pcb_Drc.check(true,false,true)};
