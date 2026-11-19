const removed=[];
for(const id of ['180da4d00c62c0a7','d77fcad73b3c2966']){const l=await eda.pcb_PrimitiveLine.get(id);if(!l)continue;if(l.getState_Net()!=='V3V3'||l.getState_Layer()!==1)throw Error('Scoped line changed');await eda.pcb_PrimitiveLine.delete(id);removed.push(id);}
for(const id of ['b7b3aa87e01bc1f6','a8a227bf7a05d7c1'])await eda.pcb_PrimitiveVia.modify(id,{diameter:18,holeDiameter:8});
const id='9c98d51399004e70',v=await eda.pcb_PrimitiveVia.get(id),ox=v.getState_X(),oy=v.getState_Y(),nx=20.4/.0254,ny=35.4/.0254;
for(const l of await eda.pcb_PrimitiveLine.getAll()){if(l.getState_Net()!=='V3V3')continue;const p={};if(Math.hypot(l.getState_StartX()-ox,l.getState_StartY()-oy)<.02){p.startX=nx;p.startY=ny;}if(Math.hypot(l.getState_EndX()-ox,l.getState_EndY()-oy)<.02){p.endX=nx;p.endY=ny;}if(Object.keys(p).length&&await eda.pcb_PrimitiveLine.get(l.getState_PrimitiveId()))await eda.pcb_PrimitiveLine.modify(l.getState_PrimitiveId(),p);}
await eda.pcb_PrimitiveVia.modify(id,{x:nx,y:ny,diameter:18,holeDiameter:8});
await eda.pcb_PrimitivePour.rebuildAllCopperRegions();await new Promise(r=>setTimeout(r,3000));
return {removed,saved:await eda.pcb_Document.save(),passed:await eda.pcb_Drc.check(true,false,false),drc:await eda.pcb_Drc.check(true,false,true),ratlines:await eda.pcb_Document.getRatlines()};
