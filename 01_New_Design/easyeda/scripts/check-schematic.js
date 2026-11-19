await eda.sch_Document.save();await new Promise(r=>setTimeout(r,3000));
const erc=await eda.sch_Drc.check(true,false,true);
const passed=await eda.sch_Drc.check(true,false,false);
const netlist=await eda.sch_ManufactureData.getNetlistFile('A3-netlist','Protel2');
const png=await eda.sch_ManufactureData.getPngFile('A3-schematic',{width:3000});
async function b64(f){if(!f)return null;return await new Promise((res,rej)=>{let r=new FileReader();r.onload=()=>res({name:f.name,size:f.size,data:r.result.split(',')[1]});r.onerror=rej;r.readAsDataURL(f);});}
return {erc,passed,netlist:netlist?await netlist.text():null,png:await b64(png)};
