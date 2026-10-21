'use strict';
// The server owns the search. Refreshing a page reconnects instead of resubmitting.
let generationPollId=null;
let generationRecoveryStarted=false;
const generationStorageKey='unisched-active-generation';
function rememberGeneration(id){try{if(id)localStorage.setItem(generationStorageKey,id);else localStorage.removeItem(generationStorageKey);}catch(_){}}
function rememberedGeneration(){try{return localStorage.getItem(generationStorageKey);}catch(_){return null;}}
function generationProgress(job){
 state.generating=true;
 openModal('Generating timetable',esc(job.name),`<div class="modal-body generation-progress"><span class="spinner"></span><h3>Coordinating your timetable…</h3><p id="job-progress">${job.elapsed_seconds||0} seconds elapsed · Search limit ${job.time_limit} seconds</p><p>Matching successful timetables are revalidated and reused when enabled.<br>You can refresh this page; it reconnects to this same search.</p><p id="job-connection" role="status"></p></div>`);
}
async function startGenerationJob(payload){
 state.generating=true;
 try{
  const job=await api('/api/generation-jobs',jsonOptions('POST',payload));
  rememberGeneration(job.id);generationProgress(job);pollGenerationJob(job.id);
 }catch(error){
  state.generating=false;
  // Another tab may already own a search with different settings. Follow it,
  // rather than creating a second search or repeatedly submitting a busy request.
  const running=await api('/api/generation-jobs/active').catch(()=>null);
  if(running?.active){rememberGeneration(running.active.id);generationProgress(running.active);pollGenerationJob(running.active.id);toast('Following the generation already running on the server.');}
  else{closeModal();render();toast(error.message);}
 }
}
async function pollGenerationJob(id){
 if(generationPollId===id)return;
 generationPollId=id;
 while(generationPollId===id){
  try{
   const response=await fetch('/api/generation-jobs/'+encodeURIComponent(id));
   const job=await response.json();
   if(response.status===404){state.generating=false;generationPollId=null;rememberGeneration(null);closeModal();render();toast(job.detail||'Server restarted. Check Version history before generating again.');return;}
   if(!response.ok)throw Error(job.detail||'Unable to read generation status.');
   if($('#job-progress'))$('#job-progress').textContent=`${job.elapsed_seconds} seconds elapsed · Search limit ${job.time_limit} seconds`;
   if($('#job-connection'))$('#job-connection').textContent='';
   if(job.status==='completed'){
    const savedResponse=await fetch('/api/generations/'+job.result_id);
    if(savedResponse.status===404){state.generating=false;generationPollId=null;rememberGeneration(null);closeModal();render();toast('The saved timetable was removed. You can generate again.');return;}
    if(!savedResponse.ok)throw Error('Unable to load saved timetable.');
    const record=await savedResponse.json();
    state.generation=record;state.history=await api('/api/generations');
    state.target=record.result.scope?.target_group_ids?.[0]||'';
    state.semester=record.config.groups.find(g=>g.id===state.target)?.semester||3;state.view='group';
    state.generating=false;generationPollId=null;rememberGeneration(null);closeModal();location.hash='timetables';render();
    toast(record.result.status==='feasible'?(record.result.summary.reused_placements?'Matching timetable revalidated and saved as a new draft.':'Timetable generated and saved.'):'The generation report explains the next steps.');return;
   }
   if(job.status==='failed'){
    state.generating=false;generationPollId=null;rememberGeneration(null);closeModal();render();toast(job.error);return;
   }
  }catch(error){if($('#job-connection'))$('#job-connection').textContent='Connection interrupted. Reconnecting to the same search…';}
  await new Promise(resolve=>setTimeout(resolve,1500));
 }
}
async function recoverGenerationJob(){
 try{
  const running=await api('/api/generation-jobs/active');
  const id=running.active?.id||rememberedGeneration();
  if(!id)return;
  const job=running.active||await api('/api/generation-jobs/'+encodeURIComponent(id));
  rememberGeneration(id);generationProgress(job);pollGenerationJob(id);
 }catch(error){rememberGeneration(null);toast(error.message);}
}
const renderBeforeGenerationJobs=render;
render=function(){
 renderBeforeGenerationJobs();
 if(state.generating)document.querySelectorAll('[data-action="generate"],[data-action="generate-scope"],[data-action="generate-division"]').forEach(b=>b.disabled=true);
 if(state.config&&!generationRecoveryStarted){generationRecoveryStarted=true;recoverGenerationJob();}
};
