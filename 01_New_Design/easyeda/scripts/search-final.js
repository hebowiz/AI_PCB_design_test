const terms=['USB-AM','USB A male SMD','AM 180','TSM-104-01-L-SV','TSM-104-01-L-SH-P','MSK12C02','MSK13C02-SZ','GRM155R71C104KA88D','GRM155R61A105KE15D','0402WGF4122TCE','0402WGF1213TCE','0402WGF2201TCE','0402WGF6801TCE','0402WGF4990TCE','BLM15AG601SN1D','USBLC6-2SC6','TPD2EUSB30','NX3225SA-12MHz-STD-CSR-6'];
const out=[];
for(const q of terms) out.push({query:q,devices:await eda.lib_Device.search(q,undefined,undefined,undefined,8,1)});
return out;
