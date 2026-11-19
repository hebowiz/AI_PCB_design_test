// Inject VIA_IDS and TARGETS from this experiment's saved evidence only.
const mm=v=>v/.0254;
const vias=[];for(const id of VIA_IDS){const v=await eda.pcb_PrimitiveVia.get(id);if(!v)throw Error('Missing candidate via '+id);vias.push(v);}
const targets=TARGETS.filter(t=>!['USB_D_N','USB_D_P'].includes(t.net));
if(vias.length!==targets.length)throw Error('Via/transition count mismatch');
const pairs=[];for(let i=0;i<vias.length;i++)for(let j=0;j<targets.length;j++)if(vias[i].getState_Net()===targets[j].net)pairs.push({i,j,d:Math.hypot(vias[i].getState_X()-mm(targets[j].p[0]),vias[i].getState_Y()-mm(targets[j].p[1]))});
pairs.sort((a,b)=>a.d-b.d);const usedV=new Set(),usedT=new Set(),changes=[];
for(const p of pairs){if(usedV.has(p.i)||usedT.has(p.j))continue;usedV.add(p.i);usedT.add(p.j);const v=vias[p.i],t=targets[p.j];changes.push({id:v.getState_PrimitiveId(),net:t.net,from:[v.getState_X()*.0254,v.getState_Y()*.0254],to:t.p});await eda.pcb_PrimitiveVia.modify(v.getState_PrimitiveId(),{x:mm(t.p[0]),y:mm(t.p[1])});}
if(usedV.size!==vias.length)throw Error('Unmatched vias');
await eda.pcb_PrimitivePour.rebuildAllCopperRegions();await new Promise(r=>setTimeout(r,3000));
return {changes,saved:await eda.pcb_Document.save(),drc:await eda.pcb_Drc.check(true,false,true),ratlines:await eda.pcb_Document.getRatlines()};
