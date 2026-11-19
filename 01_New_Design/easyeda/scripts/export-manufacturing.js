await eda.dmt_EditorControl.openDocument('6ee5c30d1c816c19');
const outputs=[];
async function add(kind,fn){try{const f=await fn();if(!f){outputs.push({kind,error:'No file returned'});return;}const data=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.onerror=reject;r.readAsDataURL(f);});outputs.push({kind,name:f.name,size:f.size,data});}catch(e){outputs.push({kind,error:String(e)});}}
await add('gerber',()=>eda.pcb_ManufactureData.getGerberFile('A3-USB-UART-Gerber.zip',false,'mm',{integerNumber:4,decimalNumber:5}));
await add('pick-place',()=>eda.pcb_ManufactureData.getPickAndPlaceFile('A3-USB-UART-PickPlace.csv','csv','mm'));
await add('bom',()=>eda.pcb_ManufactureData.getBomFile('A3-USB-UART-BOM.csv','csv'));
await add('pcb-info',()=>eda.pcb_ManufactureData.getPcbInfoFile('A3-USB-UART-PCB-info'));
await add('ipc356',()=>eda.pcb_ManufactureData.getIpcD356AFile('A3-USB-UART-testpoint.ipc'));
await add('netlist',()=>eda.pcb_ManufactureData.getNetlistFile('A3-USB-UART-PCB.net','Protel2'));
return {outputs,saved:await eda.pcb_Document.save()};
