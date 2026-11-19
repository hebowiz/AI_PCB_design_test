const mm=v=>v/.0254,net='V3V3',made=[];
const points=[['FB1',1,19.5,45.5,.6,.3],['R3',1,20,43.45,.6,.3],['U5',8,20.9,39.85,.4572,.2032],['C17',1,20.4,35.18,.6,.3],['C10',1,16.05,36.23,.6,.3]];
const cs=await eda.pcb_PrimitiveComponent.getAll();
async function line(layer,pts,w=.25){for(let i=1;i<pts.length;i++){const a=pts[i-1],b=pts[i];if(Math.hypot(a[0]-b[0],a[1]-b[1])<.001)continue;const l=await eda.pcb_PrimitiveLine.create(net,layer,mm(a[0]),mm(a[1]),mm(b[0]),mm(b[1]),mm(w),false);made.push(l.getState_PrimitiveId());}}
for(const [ref,pin,x,y,d,h] of points){const c=cs.find(c=>c.getState_Designator()===ref);const p=(await eda.pcb_PrimitiveComponent.getAllPinsByPrimitiveId(c.getState_PrimitiveId())).find(p=>p.padNumber==pin);if(p.net!==net)throw Error('Wrong pin '+ref);const v=await eda.pcb_PrimitiveVia.create(net,mm(x),mm(y),mm(h),mm(d),0,null,null,false);made.push(v.getState_PrimitiveId());await line(1,[[p.x*.0254,p.y*.0254],[x,y]],.18);}
await line(2,[[19.5,45.5],[21.3,45.5],[21.3,35.18],[20.4,35.18]]);
await line(2,[[20,43.45],[21.3,43.45]]);
await line(2,[[20.9,39.85],[21.3,39.85]]);
await line(2,[[16.05,36.23],[16.85,35.43],[20.4,35.43],[20.4,35.18]]);
await eda.pcb_PrimitivePour.rebuildAllCopperRegions();await new Promise(r=>setTimeout(r,2500));
return {made,saved:await eda.pcb_Document.save(),drc:await eda.pcb_Drc.check(true,false,true),ratlines:await eda.pcb_Document.getRatlines()};
