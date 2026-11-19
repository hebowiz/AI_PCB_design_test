const result=[];
for(const w of await eda.sch_PrimitiveWire.getAll()){
 const names=(await eda.sch_PrimitiveAttribute.getAll(w.getState_PrimitiveId())).filter(a=>a.getState_Key()==='Name'&&a.getState_Value());
 if(names.length<2)continue;
 if(names.some(a=>a.getState_Value()!==names[0].getState_Value()))throw Error('Conflicting names: '+w.getState_PrimitiveId());
 for(const a of names.slice(1)){await eda.sch_PrimitiveAttribute.modify(a.getState_PrimitiveId(),{value:'',valueVisible:false});result.push(a.getState_PrimitiveId());}
}
await new Promise(r=>setTimeout(r,2000));return {changed:result.length,saved:await eda.sch_Document.save()};
