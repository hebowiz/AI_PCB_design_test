const mm=v=>v/.0254;
const plan=[['8b9bb72ee512415b',15.2,37.25,.4572,.2032],['37eb8eae971cf669',14.8,36.7502,.4572,.2032],['289c2bdb74184c8d',15.2,36.25,.4572,.2032],['411ab414d035cbf7',13.2499,40.6002,.4572,.2032],['91d36a802755d202',14.8,37.75,.4572,.2032],['98893a6cc2a0df5a',9.25,40.6,.6,.3]];
const changes=[];
for(const [id,x,y,diameter,hole] of plan){const v=await eda.pcb_PrimitiveVia.get(id);if(!v)throw Error('Missing scoped via');const ox=v.getState_X(),oy=v.getState_Y();
 for(const l of await eda.pcb_PrimitiveLine.getAll()){if(l.getState_Net()!==v.getState_Net())continue;const p={};if(Math.hypot(l.getState_StartX()-ox,l.getState_StartY()-oy)<.02){p.startX=mm(x);p.startY=mm(y);}if(Math.hypot(l.getState_EndX()-ox,l.getState_EndY()-oy)<.02){p.endX=mm(x);p.endY=mm(y);}if(Object.keys(p).length)await eda.pcb_PrimitiveLine.modify(l.getState_PrimitiveId(),p);}
 await eda.pcb_PrimitiveVia.modify(id,{x:mm(x),y:mm(y),diameter:mm(diameter),holeDiameter:mm(hole)});changes.push({id,x,y,diameter,hole});
}
await eda.pcb_PrimitiveLine.modify('a25774a794f7834c',{endX:mm(15.2),endY:mm(37.25)});
const rc=await eda.pcb_Drc.getCurrentRuleConfiguration();const vr=rc.config.Physics['Via Size'].viaSize.form;vr.viaOuterdiameterMin=.45;vr.viaInnerdiameterMin=.2;
await eda.pcb_Drc.overwriteCurrentRuleConfiguration(rc.config);
await eda.pcb_PrimitivePour.rebuildAllCopperRegions();await new Promise(r=>setTimeout(r,2500));
return {changes,saved:await eda.pcb_Document.save(),drc:await eda.pcb_Drc.check(true,false,true),ratlines:await eda.pcb_Document.getRatlines()};
