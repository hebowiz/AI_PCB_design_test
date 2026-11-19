const queries = [
  'SN74AXC4T245', 'TLV75801PDBVR', 'AP2112K-3.3',
  'USB A male SMD', 'SS13D', 'SS12D', '12MHz 3225',
  '93LC56B', '0603 green LED', '0603 red LED', 'SMD right angle header 1x4'
].map(wd => ({wd, limit: 3}));
const groups = [];
for (const q of queries) {
  groups.push({query:q.wd, devices:await eda.lib_Device.search(q.wd,undefined,undefined,undefined,q.limit,1)});
}
return groups;
