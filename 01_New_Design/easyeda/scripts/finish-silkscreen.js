const mm=v=>v/.0254,cs=await eda.pcb_PrimitiveComponent.getAll(),pads=[],placed=[],out=[];
for(const c of cs)for(const p of await eda.pcb_PrimitiveComponent.getAllPinsByPrimitiveId(c.getState_PrimitiveId())){const b=await eda.pcb_Primitive.getPrimitivesBBox([p.primitiveId]);if(b)pads.push(b);}
function overlaps(a,b,g){return a.minX<b.maxX+g&&a.maxX>b.minX-g&&a.minY<b.maxY+g&&a.maxY>b.minY-g;}
for(const c of cs){const a=(await eda.pcb_PrimitiveAttribute.getAll(c.getState_PrimitiveId())).find(a=>a.getState_Key()==='Designator');if(!a)continue;const id=a.getState_PrimitiveId(),x=c.getState_X(),y=c.getState_Y();
 await eda.pcb_PrimitiveAttribute.modify(id,{x,y,fontSize:mm(.8),lineWidth:mm(.127),rotation:0,alignMode:5,layer:3,valueVisible:true,keyVisible:false});
 const b=await eda.pcb_Primitive.getPrimitivesBBox([id]);if(!b)throw Error('Missing text bbox');const offsets={l:b.minX-x,r:b.maxX-x,b:b.minY-y,t:b.maxY-y};
 const candidates=[];for(let dx=-7;dx<=7;dx+=.5)for(let dy=-7;dy<=7;dy+=.5)candidates.push({dx,dy,d:dx*dx+dy*dy});candidates.sort((a,b)=>a.d-b.d);
 let result;for(const p of candidates){const px=x+mm(p.dx),py=y+mm(p.dy),box={minX:px+offsets.l,maxX:px+offsets.r,minY:py+offsets.b,maxY:py+offsets.t};
  if(box.minX<mm(.35)||box.maxX>mm(21.65)||box.minY<mm(.35)||box.maxY>mm(49.65))continue;
  if(pads.some(b=>overlaps(box,b,mm(.2)))||placed.some(b=>overlaps(box,b,mm(.15))))continue;
  result={x:px,y:py,box,offsetMm:[p.dx,p.dy]};break;
 }
 if(!result)throw Error('No clear silkscreen location for '+c.getState_Designator());
 await eda.pcb_PrimitiveAttribute.modify(id,{x:result.x,y:result.y});placed.push(result.box);out.push({ref:c.getState_Designator(),id,...result});
}
const labels=[['A-3 USB UART',11,29,1,0],['22x50 / 1.6mm',11,27.5,.8,0],['VIO 1.8/2.5/3.3V',11,24.5,.8,0],['OUTPUT MAX 50mA',11,23,.8,0],['SW1  1:1.8  2:2.5  4:3.3',11,20.5,.65,0],['GND',7.19,4.5,.7,90],['TXD',9.73,4.5,.7,90],['RXD',12.27,4.5,.7,90],['5V',14.81,4.5,.7,90],['GND  RTS  CTS  VIO',11,11.6,.7,0]];
const strings=[];for(const [txt,x,y,size,rot] of labels){const s=await eda.pcb_PrimitiveString.create(4,mm(x),mm(y),txt,'default',mm(size),mm(.127),5,rot,false,0,true,false);strings.push(s.getState_PrimitiveId());}
await new Promise(r=>setTimeout(r,2500));
return {references:out,strings,saved:await eda.pcb_Document.save(),passed:await eda.pcb_Drc.check(true,false,false),drc:await eda.pcb_Drc.check(true,false,true)};
