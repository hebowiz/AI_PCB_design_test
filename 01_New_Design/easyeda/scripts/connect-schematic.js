// Pin numbers are the library/manufacturer numbers, not symbol ordering.
const nets={
 U1:{1:'XI',2:'XO',3:'VPHY',4:'GND',5:'REF12K',6:'USB_D_N',7:'USB_D_P',8:'VPLL',9:'GND',10:'GND',11:'GND',12:'V3V3',13:'TXD_3V3',14:'RXD_3V3',15:'RTS_3V3',16:'CTS_3V3',17:null,18:'UNUSED_INPUT_HIGH',19:'UNUSED_INPUT_HIGH',20:'UNUSED_INPUT_HIGH',21:null,22:'GND',23:'GND',24:'V3V3',25:'PWREN_N',26:null,27:'RXLED_N',28:'TXLED_N',29:null,30:null,31:null,32:null,33:null,34:'RESET_N',35:'GND',36:'GND',37:'VCCA_1V8',38:'VCORE_1V8',39:'V3V3',40:'V3V3',41:'GND',42:'GND',43:'EEDATA',44:'EECLK',45:'EECS',46:'V3V3',47:'GND',48:'GND',49:'GND'},
 U2:{1:'V3V3',2:'V3V3',3:'GND',4:'TXD_3V3',5:'RTS_3V3',6:'RXD_3V3',7:'CTS_3V3',8:'GND',9:'GND',10:'CTS',11:'RXD',12:'RTS',13:'TXD',14:'PWREN_N',15:'PWREN_N',16:'VIO'},
 U3:{1:'USB5V',2:'GND',3:'USB5V',4:'FB',5:'VIO'},
 U4:{1:'USB5V',2:'GND',3:'USB5V',4:null,5:'V3V3'},
 U5:{1:'EECS',2:'EECLK',3:'EEDATA',4:'EEDO',5:'GND',6:null,7:null,8:'V3V3'},
 J1:{1:'USB5V',2:'USB_D_N',3:'USB_D_P',4:'GND',5:'GND'},
 J2:{1:'GND',2:'TXD',3:'RXD',4:'USB5V_OUT'},J3:{1:'GND',2:'RTS',3:'CTS',4:'VIO_OUT'},
 D1:{1:'USB_D_P',2:'USB_D_N',3:'GND'},
 SW1:{1:'SEL_1V8',2:'SEL_2V5',3:'FB',4:null,5:'GND',6:'GND'},
 SW2:{1:'USB5V',2:'USB5V_OUT',3:null,4:'GND',5:'GND'},
 SW3:{1:'VIO',2:'VIO_OUT',3:null,4:'GND',5:'GND'},
 Y1:{1:'XI',3:'XO',2:'GND',4:'GND'},
 FB1:{1:'V3V3',2:'VPHY'},FB2:{1:'V3V3',2:'VPLL'},
 R1:{1:'REF12K',2:'GND'},R2:{1:'EEDATA',2:'EEDO'},R3:{1:'V3V3',2:'EEDO'},
 R4:{1:'V3V3',2:'PWREN_N'},R5:{1:'VIO',2:'FB'},R6:{1:'FB',2:'GND'},
 R7:{1:'VIO',2:'FB_SERIES'},R8:{1:'FB_SERIES',2:'SEL_1V8'},R9:{1:'VIO',2:'SEL_2V5'},
 R10:{1:'USB5V',2:'PWR_LED_A'},LED1:{1:'GND',2:'PWR_LED_A'},
 R11:{1:'V3V3',2:'TX_LED_A'},LED2:{1:'TXLED_N',2:'TX_LED_A'},
 R12:{1:'V3V3',2:'RX_LED_A'},LED3:{1:'RXLED_N',2:'RX_LED_A'},
 R13:{1:'V3V3',2:'RESET_N'},R14:{1:'V3V3',2:'UNUSED_INPUT_HIGH'}
};
const capNets=['USB5V','USB5V','USB5V','VIO','V3V3','VPHY','VPLL','V3V3','V3V3','V3V3','V3V3','V3V3','VCORE_1V8','VCCA_1V8','V3V3','VIO','V3V3','XI','XO'];
capNets.forEach((n,i)=>nets['C'+(i+1)]={1:n,2:'GND'});
nets.C20={1:'V3V3',2:'GND'};nets.C21={1:'VIO',2:'GND'};
const info=await eda.dmt_Project.getCurrentProjectInfo();if(info.friendlyName!=='A3-USB-UART')throw Error('Wrong project');
await eda.dmt_EditorControl.openDocument('f9bc96d854d91c11');await new Promise(r=>setTimeout(r,1500));
// This script only connects not-yet-wired pins. Existing wiring is never deleted.
let wires=await eda.sch_PrimitiveWire.getAll();
const endpoints=new Set();
for(const w of wires){const l=w.getState_Line();for(const seg of(Array.isArray(l[0])?l:[l]))for(let i=0;i<seg.length;i+=2)endpoints.add(seg[i]+','+seg[i+1]);}
const result=[];
const comps=await eda.sch_PrimitiveComponent.getAll();
for(const c of comps){
 const ref=c.getState_Designator();if(!nets[ref])continue;
 const pins=await eda.sch_PrimitiveComponent.getAllPinsByPrimitiveId(c.getState_PrimitiveId());
 for(const p of pins){try{
  const pn=p.getState_PinNumber(),net=nets[ref][pn];if(net===undefined)throw Error('Missing pin mapping '+ref+'.'+pn);
  if(net===null){const pin=p.toAsync();pin.setState_NoConnected(true);await pin.done();continue;}
  const x=p.getState_X(),y=p.getState_Y(),rot=p.getState_Rotation();
  if(endpoints.has(x+','+y))continue;
  const a=rot*Math.PI/180,ex=x+Math.round(30*Math.cos(a)),ey=y+Math.round(30*Math.sin(a));
  const w=await eda.sch_PrimitiveWire.create([x,y,ex,ey],net);if(!w)throw Error('Wire failed '+ref+'.'+pn);
  // create(line, net) already creates a Name attribute. Do not duplicate it.
  const attrs=await eda.sch_PrimitiveAttribute.getAll(w.getState_PrimitiveId());
  for(const label of attrs.filter(a=>a.getState_Key()==='Name'))
   await eda.sch_PrimitiveAttribute.modify(label.getState_PrimitiveId(),{rotation:(rot===90||rot===270)?90:0,fontSize:5});
  result.push({ref,pin:pn,net});
 }catch(e){await eda.sch_Document.save();throw Error(ref+'.'+p.getState_PinNumber()+': '+e.message);}}
 await eda.sch_Document.save();
}
await new Promise(r=>setTimeout(r,3000));
const saved=await eda.sch_Document.save();
return {saved,connections:result,expected:nets};
