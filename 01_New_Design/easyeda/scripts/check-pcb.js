await eda.pcb_Document.zoomToBoardOutline();await new Promise(r=>setTimeout(r,1500));
const drc=await eda.pcb_Drc.check(true,false,true);const passed=await eda.pcb_Drc.check(true,false,false);
const im=await eda.dmt_EditorControl.getCurrentRenderedAreaImage();
const png=im?await new Promise((res,rej)=>{let r=new FileReader();r.onload=()=>res({size:im.size,data:r.result.split(',')[1]});r.onerror=rej;r.readAsDataURL(im);}):null;
return {drc,passed,png,ratlines:await eda.pcb_Document.getRatlines(),saved:await eda.pcb_Document.save()};
