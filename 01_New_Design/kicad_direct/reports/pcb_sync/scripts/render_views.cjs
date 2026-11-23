const path=require('path');
const sharp=require('C:/Users/hebow/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=path.resolve(__dirname,'..');
(async()=>{
 for(const stage of ['before','after']){
  for(const side of ['front','back','placement']){
   const file=path.join(root,stage,side);
   const buffer=await sharp(file+'.svg',{density:600}).png().toBuffer();
   await sharp(buffer).resize({width:1400}).png().toFile(file+'.png');
   if(stage==='after'&&side==='front'){
    const {width,height}=await sharp(buffer).metadata();
    const regions={usb_power:[100,102,122,114],ft232h:[103,110,122,125],jumper_testpoints:[100,129,110,146]};
    for(const [name,[x0,y0,x1,y1]] of Object.entries(regions)){
     const left=Math.floor((x0-100)/22*width),top=Math.floor((y0-100)/50*height);
     const w=Math.min(width-left,Math.floor((x1-x0)/22*width)),h=Math.min(height-top,Math.floor((y1-y0)/50*height));
     await sharp(buffer).extract({left,top,width:w,height:h}).resize({width:1800}).png().toFile(path.join(root,stage,name+'.png'));
    }
   }
  }
 }
})();
