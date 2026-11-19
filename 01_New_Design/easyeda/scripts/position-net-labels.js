await eda.dmt_EditorControl.openDocument('f9bc96d854d91c11');await new Promise(r=>setTimeout(r,1500));
const pinMap=new Map();for(const c of await eda.sch_PrimitiveComponent.getAll('part'))for(const p of await eda.sch_PrimitiveComponent.getAllPinsByPrimitiveId(c.getState_PrimitiveId()))pinMap.set(p.getState_X()+','+p.getState_Y(),p.getState_Rotation());
let count=0;
for(const w of await eda.sch_PrimitiveWire.getAll()){
 const l=w.getState_Line();if(l.length!==4)throw Error('Review non-stub wire '+w.getState_PrimitiveId());
 let x,y,rot;if(pinMap.has(l[0]+','+l[1])){x=l[2];y=l[3];rot=pinMap.get(l[0]+','+l[1]);}else if(pinMap.has(l[2]+','+l[3])){x=l[0];y=l[1];rot=pinMap.get(l[2]+','+l[3]);}else throw Error('Unattached wire '+w.getState_PrimitiveId());
 const names=(await eda.sch_PrimitiveAttribute.getAll(w.getState_PrimitiveId())).filter(a=>a.getState_Key()==='Name'&&a.getState_Value());
 if(names.length!==1)throw Error('Expected one visible net name');
 await eda.sch_PrimitiveAttribute.modify(names[0].getState_PrimitiveId(),{x,y,fontSize:5,rotation:rot===90||rot===270?90:0,alignMode:rot===180||rot===270?9:3,valueVisible:true});count++;
}
await eda.dmt_Schematic.modifySchematicPageTitleBlock(true,{'Page Size':{showTitle:false,showValue:false,value:'A1'}});
await eda.sch_PrimitiveText.create(200,2200,'A-3 USB UART / 6 Mbps / TXD RXD RTS CTS / VIO 1.8 2.5 3.3 V',0,null,'Arial',18,true);
await eda.sch_PrimitiveText.create(2200,1800,'PCB: 22 x 50 mm, FR-4 1.6 mm, 2 layers, all parts top\nJ2: GND / TXD / RXD / USB5V_OUT\nJ3: GND / RTS / CTS / VIO_OUT\nSW1: 1.8 / 2.5 / 3.3 V; change only with target power off\nSW2 / SW3: external power outputs, max 50 mA each\nEEPROM: UART; CBUS1 PWREN#, CBUS3 RXLED#, CBUS4 TXLED#\nPrototype. Electrical performance requires hardware validation.',0,null,'Arial',10,false);
await new Promise(r=>setTimeout(r,2500));return {count,saved:await eda.sch_Document.save()};
