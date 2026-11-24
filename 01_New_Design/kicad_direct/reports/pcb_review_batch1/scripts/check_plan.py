from common import *
p=json.loads((OUT/'replacement_plan.json').read_text());uids={x['uuid'] for x in p['candidate_items']}
for uid in ['06459c4a-f22e-45bd-ba8c-b47bb14e1440','2ab96928-cb1f-4abb-9e18-08568c31702d','6ed38ab2-9f92-4ae3-a78d-0fbcdba2d319','19a261e6-918f-4fab-b196-289e63320934','618c5ece-69b9-4973-a8d3-ccd41e063b65','d155308b-077e-4271-8882-10628f85a9df','1ee53a79-3eb9-4500-b9ab-349a849a7cd1','644530fa-ced1-414f-80cc-6ac74c1ff3e6','ee10d401-ce8b-42e3-a251-7a8992a547aa']:print(uid,uid in uids)
