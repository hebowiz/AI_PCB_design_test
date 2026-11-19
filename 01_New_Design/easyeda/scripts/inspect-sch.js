const cs=await eda.sch_PrimitiveComponent.getAll();
const ws=await eda.sch_PrimitiveWire.getAll();
return {components:cs.map(c=>({ref:c.getState_Designator(),id:c.getState_PrimitiveId()})),wires:ws,attributes:await eda.sch_PrimitiveAttribute.getAll(),saved:await eda.sch_Document.save()};
