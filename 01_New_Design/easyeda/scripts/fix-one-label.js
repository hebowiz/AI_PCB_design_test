const ws=await eda.sch_PrimitiveWire.getAll();
const w=ws.find(w=>w.getState_PrimitiveId()==='c329366acac4290d');if(!w)throw Error('Wire not found');
const attrs=await eda.sch_PrimitiveAttribute.getAll(w.getState_PrimitiveId());
const names=attrs.filter(a=>a.getState_Key()==='Name');
if(names.length!==2||names.some(a=>a.getState_Value()!=='XI'))throw Error('Expected duplicate XI only');
await eda.sch_PrimitiveAttribute.modify(names[1].getState_PrimitiveId(),{key:'DuplicateLabelNote',value:'',valueVisible:false});
await new Promise(r=>setTimeout(r,1000));
return {saved:await eda.sch_Document.save(),attrs:await eda.sch_PrimitiveAttribute.getAll(w.getState_PrimitiveId())};
