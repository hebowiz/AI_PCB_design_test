const info=await eda.dmt_Project.getCurrentProjectInfo();if(info.friendlyName!=='A3-USB-UART')throw Error('Wrong project');
await eda.dmt_EditorControl.openDocument('f9bc96d854d91c11');await new Promise(r=>setTimeout(r,1500));
const schCount=(await eda.sch_PrimitiveComponent.getAll()).length,erc=await eda.sch_Drc.check(true,false,false);
const schNetFile=await eda.sch_ManufactureData.getNetlistFile('reload-sch','Protel2');const schNetlist=await schNetFile.text();
await eda.dmt_EditorControl.openDocument('6ee5c30d1c816c19');await new Promise(r=>setTimeout(r,1500));
const components=[];for(const c of await eda.pcb_PrimitiveComponent.getAll())components.push({ref:c.getState_Designator(),id:c.getState_PrimitiveId(),layer:c.getState_Layer(),x:c.getState_X(),y:c.getState_Y(),rotation:c.getState_Rotation(),pads:await eda.pcb_PrimitiveComponent.getAllPinsByPrimitiveId(c.getState_PrimitiveId())});
const lines=await eda.pcb_PrimitiveLine.getAll(),vias=await eda.pcb_PrimitiveVia.getAll(),pours=await eda.pcb_PrimitivePour.getAll();
const drc=await eda.pcb_Drc.check(true,false,false),details=await eda.pcb_Drc.check(true,false,true),ratlines=await eda.pcb_Document.getRatlines();
const pcbNetFile=await eda.pcb_ManufactureData.getNetlistFile('reload-pcb','Protel2');const pcbNetlist=await pcbNetFile.text();
const netLengths={};for(const l of lines){const n=l.getState_Net();netLengths[n]=(netLengths[n]||0)+Math.hypot(l.getState_EndX()-l.getState_StartX(),l.getState_EndY()-l.getState_StartY())*.0254;}
return {schCount,erc,schNetlist,components,lines,vias,pours,stackup:await eda.pcb_Layer.getStackup(),rules:await eda.pcb_Drc.getCurrentRuleConfiguration(),drc,details,ratlines,pcbNetlist,netLengths,saved:await eda.pcb_Document.save()};
