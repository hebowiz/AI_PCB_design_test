const terms=['USB-A male','USB-A plug','USB-A-4P','MSK-13C','MSK-12C02','SS-12F','SS-13F','TSM-104-01','TSW-104','MTSW-104','SM04B','KT-0603G','19-217/GHC','19-217/R6C','0402WGF1202TCE','0402WGF1002TCE','0402WGF4992TCE'];
const out=[];
for(const q of terms) out.push({query:q,devices:await eda.lib_Device.search(q,undefined,undefined,undefined,5,1)});
return out;
