// Exact IDs of candidate-created bottom segments, backed up before this call.
const scoped={EECLK:['6ac38a5ab29c862d','ae5a7b722ff6abd5','9f22eaee29e9901d','3038561767312139'],V3V3:['144425bd73106ef2','e04e4ad948cde79a','7eec4356297c9dc7','5e7d0ad5103756d8','5fccb0d39fc4991e','8ebc81c871bbbdeb','8e15f6ebe37cc6cc','c1e782ef4658567b','97ff2a58f2b27c6f'],GND:['5f607fa965afeca9']};
const removed=[];
for(const [net,ids]of Object.entries(scoped))for(const id of ids){const l=await eda.pcb_PrimitiveLine.get(id);if(!l)continue;if(l.getState_Net()!==net||l.getState_Layer()!==2)throw Error('Scoped segment changed');await eda.pcb_PrimitiveLine.delete(id);removed.push(id);}
const v=await eda.pcb_PrimitiveVia.get('98893a6cc2a0df5a');if(v){if(v.getState_Net()!=='GND')throw Error('Via net changed');await eda.pcb_PrimitiveVia.delete(v);removed.push(v.getState_PrimitiveId());}
await eda.pcb_PrimitivePour.rebuildAllCopperRegions();await new Promise(r=>setTimeout(r,1500));
return {removed,saved:await eda.pcb_Document.save(),drc:await eda.pcb_Drc.check(true,false,true),ratlines:await eda.pcb_Document.getRatlines(),vias:await eda.pcb_PrimitiveVia.getAll(),lines:await eda.pcb_PrimitiveLine.getAll()};
