const mm=v=>v/.0254;
await eda.dmt_EditorControl.openDocument('6ee5c30d1c816c19');
if((await eda.pcb_PrimitivePour.getAll()).length)throw Error('Ground pours already present');
const poly=eda.pcb_MathPolygon.createPolygon([mm(.4),mm(.4),'L',mm(21.6),mm(.4),mm(21.6),mm(49.6),mm(.4),mm(49.6),mm(.4),mm(.4)]);
const ids=[];
for(const layer of [1,2]) {const p=await eda.pcb_PrimitivePour.create('GND',layer,poly,'solid',false,layer===1?'GND_TOP':'GND_BOTTOM',0,mm(.254),false);ids.push(p.getState_PrimitiveId());}
const filled=await eda.pcb_PrimitivePour.rebuildAllCopperRegions();
await new Promise(r=>setTimeout(r,3000));
return {ids,filledCount:filled.length,saved:await eda.pcb_Document.save(),drc:await eda.pcb_Drc.check(true,false,true)};
