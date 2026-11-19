// Inject PLAN from reports/bottom-repair-plan.json. This changes only the scoped A-3 repair.
const mm=v=>v/.0254;
const cs=await eda.pcb_PrimitiveComponent.getAll(),c10=cs.find(c=>c.getState_Designator()==='C10');
await eda.pcb_PrimitiveComponent.modify(c10.getState_PrimitiveId(),{x:mm(17.7),y:mm(35.8),rotation:0,otherProperty:c10.getState_OtherProperty()});
await eda.pcb_PrimitiveVia.modify('37eb8eae971cf669',{x:mm(16),y:mm(36.35),diameter:18,holeDiameter:8});
await eda.pcb_PrimitiveLine.modify('12974378095974f2',{endX:mm(15.6),endY:mm(36.7502),lineWidth:5});
const made=[];
async function line(net,layer,a,b,w){if(Math.hypot(a[0]-b[0],a[1]-b[1])<.00001)return;const l=await eda.pcb_PrimitiveLine.create(net,layer,mm(a[0]),mm(a[1]),mm(b[0]),mm(b[1]),mm(w),false);made.push(l.getState_PrimitiveId());}
await line('EECLK',1,[15.6,36.7502],[16,36.35],.127);
for(const [ref,pin,x,y,d,h] of PLAN.powerPins){const c=cs.find(c=>c.getState_Designator()===ref),p=(await eda.pcb_PrimitiveComponent.getAllPinsByPrimitiveId(c.getState_PrimitiveId())).find(p=>p.padNumber==pin);if(p.net!=='V3V3')throw Error('Wrong power pin '+ref);const v=await eda.pcb_PrimitiveVia.create('V3V3',mm(x),mm(y),mm(h),mm(d),0,null,null,false);made.push(v.getState_PrimitiveId());await line('V3V3',1,[p.x*.0254,p.y*.0254],[x,y],.18);}
for(const t of PLAN.routes)for(let i=1;i<t.path.length;i++)await line(t.net,2,t.path[i-1],t.path[i],t.width);
await eda.pcb_PrimitivePour.rebuildAllCopperRegions();await new Promise(r=>setTimeout(r,3000));
return {made,saved:await eda.pcb_Document.save(),drc:await eda.pcb_Drc.check(true,false,true),ratlines:await eda.pcb_Document.getRatlines()};
