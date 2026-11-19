const erc=await eda.sch_Drc.check(true,false,true);
return {passed:await eda.sch_Drc.check(true,false,false),erc};
