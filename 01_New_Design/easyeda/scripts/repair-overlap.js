// R9 was initially coincident with U4.GND. Correct only this generated area.
const cs=await eda.sch_PrimitiveComponent.getAll();const r9=cs.find(c=>c.getState_Designator()==='R9');
if(r9.getState_Y()!==250)throw Error('Repair already applied or unexpected position');
const wires=await eda.sch_PrimitiveWire.getAll();
const affected=wires.filter(w=>{const l=w.getState_Line();return l.includes(250)&&((w.getState_Net()==='SEL_2V5')||(w.getState_Net()==='GND'&&l.includes(850)));});
for(const w of affected)await eda.sch_PrimitiveWire.delete(w.getState_PrimitiveId());
await eda.sch_PrimitiveComponent.modify(r9.getState_PrimitiveId(),{x:550,y:450,otherProperty:r9.getState_OtherProperty()});
for(const [x,y,ex,ey,n]of [[850,250,820,250,'GND'],[530,450,500,450,'VIO'],[570,450,600,450,'SEL_2V5']]){
 await eda.sch_PrimitiveWire.create([x,y,ex,ey],n);
}
return {deleted:affected.map(w=>w.getState_PrimitiveId()),saved:await eda.sch_Document.save()};
