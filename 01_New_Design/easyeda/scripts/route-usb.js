const mm=v=>v/.0254;
await eda.dmt_EditorControl.openDocument('6ee5c30d1c816c19');
if((await eda.pcb_PrimitiveLine.getAll()).some(l=>['USB_D_N','USB_D_P'].includes(l.getState_Net())))throw Error('USB routes already exist');
const cs=await eda.pcb_PrimitiveComponent.getAll(),pads={};
for(const c of cs)for(const p of await eda.pcb_PrimitiveComponent.getAllPinsByPrimitiveId(c.getState_PrimitiveId()))pads[c.getState_Designator()+'.'+p.padNumber]=[p.x*.0254,p.y*.0254];
const made=[];
async function line(net,layer,points,width=.18){for(let i=1;i<points.length;i++){const a=points[i-1],b=points[i];const l=await eda.pcb_PrimitiveLine.create(net,layer,mm(a[0]),mm(a[1]),mm(b[0]),mm(b[1]),mm(width),true);made.push(l.getState_PrimitiveId());}}
async function via(net,x,y){const v=await eda.pcb_PrimitiveVia.create(net,mm(x),mm(y),mm(.3),mm(.6),0,null,null,true);made.push(v.getState_PrimitiveId());}
await line('USB_D_N',1,[pads['J1.2'],[10,43.5],[9.8,43.3],[9.8,42.9],[10.35,42.35],[11.35,42.35],pads['D1.2'],[11.35,40.6],pads['U1.6']]);
await line('USB_D_P',1,[pads['J1.3'],[12,42.8]]);
await via('USB_D_P',12,42.8);await via('USB_D_P',10.65,41.25);
await line('USB_D_P',2,[[12,42.8],[12,42.6],[10.65,41.25]]);
await line('USB_D_P',1,[pads['D1.1'],[10.65,41.25],[10.65,40.6],pads['U1.7']]);
await new Promise(r=>setTimeout(r,2500));
return {made,saved:await eda.pcb_Document.save(),drc:await eda.pcb_Drc.check(true,false,true),note:'Short prototype USB routing with polarity crossover; impedance and eye diagram are unverified.'};
