"""A-2 circuit data. Units: mm; PCB origin is (100, 100), top view.

User amendment: only TXD/RXD/RTS/CTS are exposed. No atopile dependency.
"""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
KICAD = Path(os.environ.get('KICAD_ROOT', str(Path(os.environ['LOCALAPPDATA'])/'Programs/KiCad/10.0')))
PARTS = []

def part(ref, value, lib, footprint, nets, xy, angle=0, mpn='', note='', group='support'):
    PARTS.append(dict(ref=ref,value=value,lib=lib,footprint=footprint,
                      nets={str(k):v for k,v in nets.items()},xy=xy,angle=angle,
                      mpn=mpn,note=note,group=group))

part('U1','FT232HL','A2:FT232HL_UART','Package_QFP:LQFP-48_7x7mm_P0.5mm',{
  1:'XTAL_IN',2:'XTAL_OUT',3:'VPHY',4:'GND',5:'REF12K',6:'USB_D-',7:'USB_D+',8:'VPLL',9:'GND',10:'GND',11:'GND',12:'+3V3',
  13:'FT_TXD',14:'FT_RXD',15:'FT_RTS_N',16:'FT_CTS_N',17:None,18:None,19:None,20:None,21:None,22:'GND',23:'GND',24:'+3V3',
  25:None,26:None,27:'RXLED_N',28:'TXLED_N',29:None,30:None,31:None,32:'PWREN_N',33:None,34:'RESET_N',35:'GND',36:'GND',
  37:'VCCA_1V8',38:'VCORE_1V8',39:'+3V3',40:'+3V3',41:'GND',42:'GND',43:'EE_DATA',44:'EE_CLK',45:'EE_CS',46:'+3V3',47:'GND',48:'GND'},(11,16),270,'FT232HL-REEL','UART mode; EEPROM programming required','bridge')
part('U2','SN74AXC4T245PWR','A2:SN74AXC4T245','Package_SO:TSSOP-16_4.4x5mm_P0.65mm',{
 1:'+3V3',2:'+3V3',3:'GND',4:'FT_TXD',5:'FT_RTS_N',6:'FT_RXD',7:'FT_CTS_N',8:'GND',9:'GND',10:'CTS_N',11:'RXD',12:'RTS_N',13:'TXD',14:'PWREN_N',15:'PWREN_N',16:'VIO'},(11,29),0,'SN74AXC4T245PWR','1DIR=1 (TX/RTS); 2DIR=0 (RX/CTS)','uart')
part('U3','AP2112K-3.3','Regulator_Linear:AP2112K-3.3','Package_TO_SOT_SMD:SOT-23-5',{1:'USB5V',2:'GND',3:'USB5V',4:None,5:'+3V3'},(18.5,8.5),0,'AP2112K-3.3TRG1','Fixed bridge supply','power')
part('U4','TLV75801PDBV','Regulator_Linear:TLV75801PDBV','Package_TO_SOT_SMD:SOT-23-5',{1:'USB5V',2:'GND',3:'PWR_EN',4:'FB',5:'VIO'},(11,37),0,'TLV75801PDBVR','1.8/2.5/3.3 V; change SW1 only while unpowered','power')
part('U5','93LC56B','Memory_EEPROM:93LCxxB','Package_SO:MSOP-8_3x3mm_P0.65mm',{1:'EE_CS',2:'EE_CLK',3:'EE_DATA',4:'EE_DO',5:'GND',6:None,7:None,8:'+3V3'},(4.5,23),0,'93LC56B-I/MS','16-bit organization','bridge')
part('U6','TPS22919DCK','Power_Management:TPS22919DCK','Package_TO_SOT_SMD:SOT-363_SC-70-6',{1:'USB5V',2:'GND',3:'PWR_EN',4:None,5:'QOD',6:'USB5V_ENABLED'},(3.5,34),0,'TPS22919DCKR','USB external power disabled before enumeration / in suspend','power')
part('Q1','2N7002','Transistor_FET:2N7002','Package_TO_SOT_SMD:SOT-23',{1:'PWREN_N',2:'GND',3:'PWR_EN'},(17,23),0,'2N7002P,215','Invert PWREN# for load switch and adjustable LDO','power')
part('D1','TPD2EUSB30','Power_Protection:TPD2EUSB30','Package_TO_SOT_SMD:Texas_DRT-3',{1:'USB_D+',2:'USB_D-',3:'GND'},(11,7.5),0,'TPD2EUSB30DRTR','USB ESD','bridge')
part('J1','USB-A PLUG','A2:USB_A_PLUG','Connector_USB:USB_A_Molex_48037-2200_Horizontal',{1:'USB5V',2:'USB_D-',3:'USB_D+',4:'GND','SH':'GND'},(11,-7.225),90,'0480372200','Vendor recommended 1.6 mm PCB adopted; mechanical fit requires prototype check','bridge')
part('J2','GND TXD RXD 5V','Connector_Generic:Conn_01x04','A2:TSM_104_SH_PROVISIONAL',{1:'GND',2:'TXD',3:'RXD',4:'USB5V_OUT'},(11,47),0,'TSM-104-01-T-SH','PROVISIONAL footprint; manufacturer land-pattern confirmation required','uart')
part('J3','RTS CTS GND VIO','Connector_Generic:Conn_01x04','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical_SMD_Pin1Left',{1:'RTS_N',2:'CTS_N',3:'GND',4:'VIO_OUT'},(11,42),90,'TSM-104-01-T-SV','Generic KiCad land pattern; confirm exact part before fab','uart')
part('SW1','1V8 / 2V5 / 3V3','A2:PCM13','Button_Switch_SMD:SW_SP3T_PCM13',{1:None,2:'FB_2V5',3:'GND',4:'FB_3V3'},(19.7,34),90,'PCM13SMTR','Common pin 3; pos1=1-3, pos2=2-3, pos3=3-4','power')
part('SW2','USB5V OUT','A2:PCM12','Button_Switch_SMD:SW_SPDT_PCM12',{1:None,2:'USB5V_OUT',3:'USB5V_ENABLED'},(2.3,42),270,'PCM12SMTR','Off/open or on; no external back-feed permitted','power')
part('SW3','VIO OUT','A2:PCM12','Button_Switch_SMD:SW_SPDT_PCM12',{1:None,2:'VIO_OUT',3:'VIO'},(19.7,44.5),90,'PCM12SMTR','Switches header supply only; UART remains enabled','power')
part('Y1','12MHz 18pF','Device:Crystal_GND24','Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',{1:'XTAL_IN',2:'GND',3:'XTAL_OUT',4:'GND'},(4.3,10),0,'ABM8-12.000MHZ-B2-T','27 pF loads assume 4.5 pF stray; frequency/start-up requires measurement','bridge')

def r(ref,val,a,b,xy,angle=0,mpn='',note=''):
    part(ref,val,'Device:R','Resistor_SMD:R_0402_1005Metric',{1:a,2:b},xy,angle,mpn or f'Yageo RC0402FR-07 ({val}, 1%)',note)
def c(ref,val,a,xy,angle=0,large=False,mpn=''):
    part(ref,val,'Device:C',f'Capacitor_SMD:C_{"0603_1608" if large else "0402_1005"}Metric',{1:a,2:'GND'},xy,angle,mpn or ('GRM188R61A225KE34D' if val=='2.2u' else 'CL05B104KO5NNNC' if val=='100n' else 'C1005C0G1H270J050BA' if val=='27p' else 'CL05A105KA5NQNC'),'Capacitance at DC bias must meet regulator minimum')
r('R1','12k','REF12K','GND',(7,10.8),90,'RC0402FR-0712KL')
r('R2','10k','+3V3','RESET_N',(18,15),90,'RC0402FR-0710KL')
r('R3','10k','+3V3','EE_DO',(2,27),90,'RC0402FR-0710KL')
r('R4','2.2k','EE_DO','EE_DATA',(5,27),0,'RC0402FR-072K2L')
r('R5','10k','+3V3','PWREN_N',(17,26),0,'RC0402FR-0710KL')
r('R6','10k','+3V3','PWR_EN',(19.5,23),90,'RC0402FR-0710KL')
r('R7','22.6k','VIO','FB',(14.2,36),90,'RC0402FR-0722K6L')
r('R8','10k','FB','GND',(14.2,38.5),90,'RC0402FR-0710KL')
r('R9','17.8k','FB','FB_2V5',(16.3,33.5),90,'RC0402FR-0717K8L')
r('R10','8.25k','FB','FB_3V3',(16.3,37),90,'RC0402FR-078K25L')
r('R11','100k','VIO','RXD',(15.5,29),90,'RC0402FR-07100KL')
r('R12','100k','VIO','CTS_N',(15.5,31.5),90,'RC0402FR-07100KL')
r('R13','10k','USB5V','LED_PWR_A',(19,3),0,'RC0402FR-0710KL','About 0.3 mA red indicator')
r('R14','4.7k','+3V3','LED_TX_A',(18.5,18),90,'RC0402FR-074K7L','About 0.28 mA green indicator')
r('R15','4.7k','+3V3','LED_RX_A',(20.2,18),90,'RC0402FR-074K7L','About 0.28 mA green indicator')
r('R16','100','QOD','USB5V_ENABLED',(6,34),90,'RC0402FR-07100RL','Discharge resistor')
for ref,color,an,ka,xy,mpn in [('D2','RED','LED_PWR_A','GND',(19,5),'LTST-C190KRKT'),('D3','GREEN TX','LED_TX_A','TXLED_N',(18.5,20.5),'LTST-C190KGKT'),('D4','GREEN RX','LED_RX_A','RXLED_N',(20.2,20.5),'LTST-C190KGKT')]:
    part(ref,color,'Device:LED','LED_SMD:LED_0603_1608Metric',{1:ka,2:an},xy,90,mpn,'1608M; visual brightness unverified')

c('C1','1u','USB5V',(16,7),90)
c('C2','2.2u','+3V3',(18.5,11.5),0,True)
c('C3','100n','+3V3',(15,9.6),0)
c('C4','100n','+3V3',(4.5,15),90)
c('C5','100n','+3V3',(17.7,13),0)
c('C6','100n','+3V3',(11,22.5),0)
c('C7','100n','VCCA_1V8',(15,21.5),90)
c('C8','100n','VCORE_1V8',(13.3,21.5),90)
c('C9','100n','VPHY',(6,7),0)
c('C10','100n','VPLL',(13.5,9),90)
c('C11','1u','VPHY',(7.7,7),0)
c('C12','1u','VPLL',(15,7),90)
c('C13','27p','XTAL_IN',(2,7.8),90)
c('C14','27p','XTAL_OUT',(2,12.4),90)
c('C15','100n','+3V3',(4,19.3),0)
c('C16','100n','+3V3',(6.7,25.3),90)
c('C17','100n','VIO',(15.5,26.7),90)
c('C18','1u','USB5V',(8,34.5),0)
c('C19','2.2u','VIO',(10.7,33.8),0,True)
c('C20','1u','USB5V',(2.8,31.2),0)
c('C21','1u','USB5V_ENABLED',(5.5,36.5),90)
c('C22','100n','RESET_N',(20,15),90)
for ref,net,xy in [('FB1','VPHY',(9,8.8)),('FB2','VPLL',(13.5,6))]:
    part(ref,'600R@100MHz','Device:FerriteBead','Inductor_SMD:L_0402_1005Metric',{1:'+3V3',2:net},xy,0,'BLM15AG601SN1D','Local PHY / PLL filtering')

# Explicit ERC power sources after passive beads and the USB connector.
FLAGS = ['USB5V','GND','VPHY','VPLL']

# Placement refinement after initial KiCad DRC (no manual CAD edits occurred).
REVISED = {'J1':(11,-6.225),'C13':(1.6,7.2),'C14':(1.6,13),
           'C1':(16.3,5.8),'C11':(8,6.8),'C8':(13,23.8),'C7':(15.2,23.8),
           'Q1':(18.5,24),'R6':(20.5,26.4),'R5':(18.2,26.8),
           'C16':(7.2,24),'J3':(11,42.6),'R8':(14.2,38),
           'U4':(10.5,36.2),'C19':(10.7,33.8),'J3':(11,42.1),
           'FB2':(13,7.5),'C12':(20.5,12.3),'C16':(8.5,24),
           'C19':(10.7,33.5),'C18':(7,34.3),'R8':(14.7,37.4),
           'J2':(11,47.3),'J3':(11,42),'R7':(14.2,35.2),'C18':(8,32.6)}
for p in PARTS:
    if p['ref'] in REVISED:p['xy']=REVISED[p['ref']]
