const info=await eda.dmt_Project.getCurrentProjectInfo();if(info.friendlyName!=='A3-USB-UART')throw Error('Wrong project');
await eda.dmt_EditorControl.openDocument('6ee5c30d1c816c19');await new Promise(r=>setTimeout(r,2000));
const existing=await eda.pcb_PrimitiveComponent.getAll();if(existing.length)throw Error('PCB is not empty; review first');
const imported=await eda.pcb_Document.importChanges('bf082de2abf7fb8d',true);
await new Promise(r=>setTimeout(r,4000));
const out=[];for(const c of await eda.pcb_PrimitiveComponent.getAll())out.push({ref:c.getState_Designator(),id:c.getState_PrimitiveId(),x:c.getState_X(),y:c.getState_Y(),rotation:c.getState_Rotation(),pads:await eda.pcb_PrimitiveComponent.getAllPinsByPrimitiveId(c.getState_PrimitiveId())});
return {imported,saved:await eda.pcb_Document.save(),components:out,layers:await eda.pcb_Layer.getAllLayers(),stackup:await eda.pcb_Layer.getStackup(),rules:await eda.pcb_Drc.getCurrentRuleConfiguration(),netRules:await eda.pcb_Drc.getNetRules()};
