await eda.dmt_EditorControl.openDocument('6ee5c30d1c816c19');
await new Promise(r=>setTimeout(r,1500));
return await eda.pcb_Document.startAutoRouting({RoutingNets:['XI','XO','VPHY','VPLL','REF12K'],layers:[1,2],cornerStyle:0,existingPrimitiveMode:'keep',optimization:0});
