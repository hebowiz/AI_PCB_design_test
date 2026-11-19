const info=await eda.dmt_Project.getCurrentProjectInfo();if(info.friendlyName!=='A3-USB-UART')throw Error('Wrong project');
const comps=await eda.sch_PrimitiveComponent.getAll('part');
if(comps.find(c=>c.getState_Designator()==='U1').getState_Y()!==800)throw Error('Reflow already applied');
const before=await eda.sch_ManufactureData.getNetlistFile('before-reflow','Protel2');
const ws=await eda.sch_PrimitiveWire.getAll();
const wireSnapshot=ws.map(w=>({id:w.getState_PrimitiveId(),net:w.getState_Net(),line:w.getState_Line()}));
const changedLabels=[];
// Preserve every wire and net; only blank the identical duplicate Name value.
for(const w of ws){
 const attrs=await eda.sch_PrimitiveAttribute.getAll(w.getState_PrimitiveId());
 const names=attrs.filter(a=>a.getState_Key()==='Name'&&a.getState_Value());
 if(names.length>1){
  if(names.some(a=>a.getState_Value()!==names[0].getState_Value()))throw Error('Conflicting net names; stop');
  for(const a of names.slice(1)){await eda.sch_PrimitiveAttribute.modify(a.getState_PrimitiveId(),{value:'',valueVisible:false});changedLabels.push(a.getState_PrimitiveId());}
 }
}
for(const c of comps){
 const ref=c.getState_Designator();
 await eda.sch_PrimitiveComponent.modify(c.getState_PrimitiveId(),{x:c.getState_X()+200,y:c.getState_Y()+650+(ref==='LED1'?8:0),otherProperty:c.getState_OtherProperty()});
}
for(const w of wireSnapshot){
 const l=w.line.map((v,i)=>i%2===0?v+200:v+650+(v===192?8:0));
 await eda.sch_PrimitiveWire.modify(w.id,{line:l,net:w.net});
 const attrs=await eda.sch_PrimitiveAttribute.getAll(w.id);
 for(const a of attrs.filter(a=>a.getState_Key()==='Name'&&a.getState_Value()))
  await eda.sch_PrimitiveAttribute.modify(a.getState_PrimitiveId(),{fontSize:5,rotation:l[0]===l[2]?90:0});
}
await eda.dmt_Schematic.modifySchematicPageTitleBlock(true,{Size:{showTitle:true,showValue:true,value:'A1'},Company:{showTitle:false,showValue:true,value:'Independent A-3 experiment'},Version:{showTitle:true,showValue:true,value:'A3-r1 / DRAFT'}});
await new Promise(r=>setTimeout(r,3000));
const afterWires=await eda.sch_PrimitiveWire.getAll();
if(afterWires.length!==ws.length)throw Error('Wire count changed');
return {before:await before.text(),preservedWires:ws.length,changedLabels,saved:await eda.sch_Document.save()};
