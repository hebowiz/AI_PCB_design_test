const info=await eda.dmt_Project.getCurrentProjectInfo();
if(info.friendlyName!=='A3-USB-UART')throw new Error('Wrong project');
await eda.dmt_EditorControl.openDocument('f9bc96d854d91c11');
await new Promise(r=>setTimeout(r,1500));
const plan=[
 ['J1','AM 180',150,1150],['J2','TSM-104-01-L-SH-P',1450,1000],['J3','TSM-104-01-L-SV',1450,800],
 ['SW1','MSK13C02-SZ',800,400],['SW2','MINI MSK12CO2',1100,400],['SW3','MINI MSK12CO2',1400,400],
 ['D1','TPD2EUSB30ADRTR',150,1000],['LED1','19-217/R6C-AL1M2VY/3T',1400,200],
 ['LED2','19-217/GHC-YR1S2/3T',1100,200],['LED3','19-217/GHC-YR1S2/3T',1100,50],
 ['Y1','NX3225SA-12MHz-STD-CSR-6',150,600],
 ['FB1','BLM15AG601SN1D',500,1200],['FB2','BLM15AG601SN1D',750,1200],
 ['R1','0402WGF1202TCE',350,600],['R2','0402WGF2201TCE',150,400],
 ['R3','0402WGF1002TCE',150,250],['R4','0402WGF1002TCE',850,1000],
 ['R5','0402WGF4992TCE',500,100],['R6','0402WGF1002TCE',500,-50],
 ['R7','0402WGF4122TCE',750,100],['R8','0402WGF4990TCE',750,-50],
 ['R9','0402WGF1213TCE',850,250],['R10','0402WGF6801TCE',1400,50],
 ['R11','0402WGF2201TCE',1100,-100],['R12','0402WGF2201TCE',1400,-100],
 ['R13','0402WGF1002TCE',350,1000],['R14','0402WGF1002TCE',350,400],
 ['C1','GRM155R61A105KE15D',150,1350],['C2','GRM155R61A105KE15D',450,1350],
 ['C3','GRM155R61A105KE15D',750,1350],['C4','GRM155R61A105KE15D',1050,1350],
 ['C5','GRM155R61A105KE15D',1350,1350],
];
for(let i=6;i<=17;i++)plan.push(['C'+i,'GRM155R71C104KA88D',150+((i-6)%6)*250,-300-Math.floor((i-6)/6)*140]);
plan.push(['C18','GRM1555C1H100JA01D',150,100],['C19','GRM1555C1H100JA01D',150,-50]);
const existing=await eda.sch_PrimitiveComponent.getAll();const refs=new Set(existing.map(c=>c.getState_Designator()));
const cache=new Map(),out=[];
for(const [ref,key,x,y]of plan){
 if(refs.has(ref))continue;
 let d=cache.get(key);if(!d){const ds=await eda.lib_Device.search(key,undefined,undefined,undefined,10,1);d=ds.find(v=>v.name===key);if(!d)throw new Error('Missing exact part '+key);cache.set(key,d);}
 const c=await eda.sch_PrimitiveComponent.create(d,x,y,undefined,0,false,true,true);const id=c.getState_PrimitiveId();
 const prop=(await eda.sch_PrimitiveComponent.get(id)).getState_OtherProperty();
 await eda.sch_PrimitiveComponent.modify(id,{designator:ref,otherProperty:prop});
 out.push({ref,id,part:d.name,supplierId:d.supplierId,pins:await eda.sch_PrimitiveComponent.getAllPinsByPrimitiveId(id)});
 if(out.length%8===0)await eda.sch_Document.save();
}
return {saved:await eda.sch_Document.save(),components:out};
