// Targeted moves of this experiment's generated components; preserve other objects.
const mm=v=>v/.0254;
await eda.dmt_EditorControl.openDocument('6ee5c30d1c816c19');
const plan={SW1:[2.4,17.5,270],SW2:[2.4,6,270],SW3:[19.6,6,90],U5:[18.6,38.8,270],C10:[16.05,36.65,90],C6:[12.8,41.25,0],R1:[14.3,41.1,90],FB1:[19.5,46,90],FB2:[6,42,90],D1:[11,42.4,270],R2:[20.5,42,90]};
const changes=[];
for(const c of await eda.pcb_PrimitiveComponent.getAll()) {const ref=c.getState_Designator(),p=plan[ref];if(!p)continue;
 changes.push({ref,from:[c.getState_X(),c.getState_Y(),c.getState_Rotation()],toMm:p});
 await eda.pcb_PrimitiveComponent.modify(c.getState_PrimitiveId(),{x:mm(p[0]),y:mm(p[1]),rotation:p[2],otherProperty:c.getState_OtherProperty()});
}
await new Promise(r=>setTimeout(r,2000));
return {changes,saved:await eda.pcb_Document.save(),drc:await eda.pcb_Drc.check(true,false,true)};
