// The public job log exposes a tentative route. Capture it for review, not as a completed job.
let best=null;
const started=Date.now();
while(Date.now()-started<45000){
 const status=await eda.pcb_Document.getAutoJobStatus('autoroute-2');
 const log=await eda.pcb_Document.getAutoJobLog('autoroute-2');
 const r=log?.result;
 if(r&&(!best||r.routabitity>best.candidate.routabitity))best={candidate:JSON.parse(JSON.stringify(r)),status,capturedAt:new Date().toISOString()};
 if(status.state!=='running'||best?.candidate.routabitity>=.99)break;
 await new Promise(r=>setTimeout(r,1000));
}
return best;
