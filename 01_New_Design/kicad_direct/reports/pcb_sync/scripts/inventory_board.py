from pathlib import Path
import json, xml.etree.ElementTree as E, pcbnew as p
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'reports/pcb_sync'
b=p.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'))
x=E.parse(OUT/'approved.xml').getroot()
components={c.get('ref'):{'value':c.findtext('value'),'footprint':c.findtext('footprint'),'fields':{f.get('name'):f.text or '' for f in c.findall('fields/field')},'properties':{f.get('name'):f.get('value','') for f in c.findall('property')},'uuid':c.findtext('tstamps'),'sheet':c.find('sheetpath').get('tstamps')} for c in x.findall('components/comp')}
terminals={}
for net in x.findall('nets/net'):
 for n in net.findall('node'): terminals[f"{n.get('ref')}.{n.get('pin')}"]=net.get('name')
def pos(v):return [round(p.ToMM(v.x),6),round(p.ToMM(v.y),6)]
footprints={f.GetReference():{'value':f.GetValue(),'footprint':f.GetFPID().GetUniStringLibId(),'uuid':f.m_Uuid.AsString(),'path':f.GetPath().AsString(),'pos':pos(f.GetPosition()),'angle':f.GetOrientationDegrees(),'dnp':f.IsDNP(),'pads':{a.GetNumber():{'net':a.GetNetname(),'pos':pos(a.GetPosition()),'size':pos(a.GetSize()),'uuid':a.m_Uuid.AsString()} for a in f.Pads()}} for f in b.GetFootprints()}
tracks=[{'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'start':pos(t.GetStart()),'end':pos(t.GetEnd()),'layer':b.GetLayerName(t.GetLayer()),'width':p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()),'via':isinstance(t,p.PCB_VIA)} for t in b.GetTracks()]
changes={}
for ref in sorted(set(components)|set(footprints)):
 c=components.get(ref);f=footprints.get(ref)
 if c is None:changes[ref]={'removed':f};continue
 if f is None:changes[ref]={'added':c};continue
 d={k:{'pcb':f[k],'schematic':c[k]} for k in ['value','footprint'] if f[k]!=c[k]}
 pd={num:{'pcb':a['net'],'schematic':terminals.get(ref+'.'+num,'')} for num,a in f['pads'].items() if a['net']!=terminals.get(ref+'.'+num,'')}
 if pd:d['pads']=pd
 if d:changes[ref]=d
snapshot={'components':components,'terminals':terminals,'footprints':footprints,'tracks':tracks,'thickness':p.ToMM(b.GetDesignSettings().GetBoardThickness()),'layers':b.GetCopperLayerCount(),'zones':[{'uuid':z.m_Uuid.AsString(),'net':z.GetNetname(),'layer':b.GetLayerName(z.GetLayer())} for z in b.Zones()]}
(OUT/'before/inventory.json').write_text(json.dumps(snapshot,indent=2,ensure_ascii=False),encoding='utf-8')
(OUT/'schematic_pcb_difference.json').write_text(json.dumps(changes,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(changes,indent=2,ensure_ascii=False))
print('COUNTS',len(components),len(footprints),len(tracks),'thickness/layers',snapshot['thickness'],snapshot['layers'])
print('PLACEMENTS',json.dumps({r:(f['pos'],f['angle']) for r,f in footprints.items()}))
