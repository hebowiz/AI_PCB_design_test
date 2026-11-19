const plan=[['C20','GRM188R60J475KE19D',1900,1500],['C21','GRM155R61A105KE15D',1900,1300]];
const out=[];
const refs=new Set((await eda.sch_PrimitiveComponent.getAll('part')).map(c=>c.getState_Designator()));
for(const[ref,key,x,y]of plan){if(refs.has(ref))continue;const ds=await eda.lib_Device.search(key,undefined,undefined,undefined,10,1);const d=ds.find(d=>d.name===key);if(!d)throw Error('Part not found '+key);
 const c=await eda.sch_PrimitiveComponent.create(d,x,y,undefined,0,false,true,true);const id=c.getState_PrimitiveId();const prop=(await eda.sch_PrimitiveComponent.get(id)).getState_OtherProperty();
 await eda.sch_PrimitiveComponent.modify(id,{designator:ref,otherProperty:prop});out.push({ref,part:key,supplierId:d.supplierId});}
await new Promise(r=>setTimeout(r,3000));return {out,saved:await eda.sch_Document.save()};
