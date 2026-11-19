const info = await eda.dmt_Project.getCurrentProjectInfo();
if (info.friendlyName !== 'A3-USB-UART') throw new Error('Wrong project');
const page = info.data[0].schematic.page[0].uuid;
await eda.dmt_EditorControl.openDocument(page);
await new Promise(r=>setTimeout(r,2500));
const existing = await eda.sch_PrimitiveComponent.getAll();
if (existing.some(c=>c.getState_Designator()==='U1')) throw new Error('Core already placed');
const plan = [
 ['U1','FT232HQ-REEL',550,800],
 ['U2','SN74AXC4T245PWR',1100,800],
 ['U3','TLV75801PDBVR',500,250],
 ['U4','AP2112K-3.3TRG1',900,250],
 ['U5','93LC56B-I/MS',150,800]
];
const out=[];
for (const [ref,key,x,y] of plan) {
 const found=await eda.lib_Device.search(key,undefined,undefined,undefined,10,1);
 const dev=found.find(d=>d.name===key);
 if(!dev) throw new Error('Missing exact part '+key);
 const c=await eda.sch_PrimitiveComponent.create(dev,x,y,undefined,0,false,true,true);
 const id=c.getState_PrimitiveId();
 const prop=(await eda.sch_PrimitiveComponent.get(id)).getState_OtherProperty();
 await eda.sch_PrimitiveComponent.modify(id,{designator:ref,otherProperty:prop});
 out.push({ref,id,device:dev.name,supplierId:dev.supplierId,pins:await eda.sch_PrimitiveComponent.getAllPinsByPrimitiveId(id)});
}
const saved=await eda.sch_Document.save();
return {saved,page,components:out};
