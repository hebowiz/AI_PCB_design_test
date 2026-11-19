const mm=v=>v/0.0254;
await eda.dmt_EditorControl.openDocument('6ee5c30d1c816c19');await new Promise(r=>setTimeout(r,1500));
if((await eda.pcb_PrimitivePolyline.getAll()).length)throw Error('PCB already has geometry; review first');
await eda.pcb_Layer.setTheNumberOfCopperLayers(2);
await eda.pcb_PrimitivePolyline.create('',11,eda.pcb_MathPolygon.createPolygon([0,0,'L',mm(22),0,mm(22),mm(50),0,mm(50),0,0]),mm(.05),true);
const plan={
 J1:[11,46.5,180],J2:[11,2.2,0],J3:[11,8.5,0],U1:[11,36,180],U2:[7,26,180],U3:[12,16,0],U4:[19,28.5,90],U5:[19,38.5,270],
 SW1:[2,17.5,270],SW2:[2,6,270],SW3:[20,6,90],D1:[11,43.4,0],Y1:[17,43,0],
 LED1:[19.5,20,0],LED2:[19.5,23,0],LED3:[19.5,25.5,0],
 FB1:[15.2,45,0],FB2:[7,44,0],R1:[13.7,41.6,90],R2:[19,42,0],R3:[20,44,90],R4:[7,31,0],
 R5:[14.5,17.5,90],R6:[14.5,15,90],R7:[7,18,0],R8:[7,16.5,0],R9:[7,15,0],
 R10:[17,20,0],R11:[17,23,0],R12:[17,25.5,0],R13:[13.3,30.3,0],R14:[5.3,35,90],
 C1:[6,46,90],C2:[9,16,90],C3:[19,31.2,0],C4:[14.5,12.8,0],C5:[16.3,28.5,90],
 C6:[13.5,40.5,0],C7:[8.5,41,0],C8:[6.5,40,90],C9:[5.8,32.8,90],C10:[16.2,37.7,0],
 C11:[16.2,34.2,0],C12:[16.2,35.5,0],C13:[16.2,32.8,0],C14:[16.2,31.5,0],
 C15:[10.3,29.5,0],C16:[10.3,22.7,0],C17:[20.4,35.7,90],C18:[15,43,90],C19:[17,45.3,90],
 C20:[14,28.5,90],C21:[12,12.8,0]
};
const cs=await eda.pcb_PrimitiveComponent.getAll();const out=[];
for(const c of cs){const ref=c.getState_Designator(),p=plan[ref];if(!p)throw Error('No placement '+ref);
 await eda.pcb_PrimitiveComponent.modify(c.getState_PrimitiveId(),{x:mm(p[0]),y:mm(p[1]),rotation:p[2],layer:1,otherProperty:c.getState_OtherProperty()});
 const attrs=await eda.pcb_PrimitiveAttribute.getAll(c.getState_PrimitiveId());
 for(const a of attrs){if(a.getState_Key()==='Designator')await eda.pcb_PrimitiveAttribute.modify(a.getState_PrimitiveId(),{fontSize:mm(.65),lineWidth:mm(.127),valueVisible:true});else if(a.getState_Key()==='Name')await eda.pcb_PrimitiveAttribute.modify(a.getState_PrimitiveId(),{valueVisible:false});}
 out.push({ref,mm:p,id:c.getState_PrimitiveId()});
}
const current=await eda.pcb_Drc.getCurrentRuleConfiguration();const r=current.config;
const safe=r.Spacing['Safe Spacing'].copperThickness1oz.tables['1'].content;
for(let i=0;i<7;i++)for(let j=0;j<safe[i].length;j++)safe[i][j]=.127;
r.Physics.Track.copperThickness1oz.form.data['1']={minValue:.127,defaultValue:.18,maxValue:2.54};
const vr=r.Physics['Via Size'].viaSize.form;vr.viaOuterdiameterMin=.6;vr.viaOuterdiameterDefault=.6;vr.viaInnerdiameterMin=.3;vr.viaInnerdiameterDefault=.3;
await eda.pcb_Drc.overwriteCurrentRuleConfiguration(r);
await new Promise(r=>setTimeout(r,4000));
const components=[];for(const c of await eda.pcb_PrimitiveComponent.getAll())components.push({ref:c.getState_Designator(),id:c.getState_PrimitiveId(),bbox:await eda.pcb_Primitive.getPrimitivesBBox([c.getState_PrimitiveId()]),pads:await eda.pcb_PrimitiveComponent.getAllPinsByPrimitiveId(c.getState_PrimitiveId())});
return {saved:await eda.pcb_Document.save(),placements:out,components,stackup:await eda.pcb_Layer.getStackup()};
