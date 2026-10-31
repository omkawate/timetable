'use strict';
async function loadFacultyDetails(){
 const node=document.getElementById('faculty-load-details');if(!node)return;
 try{const rows=await api('/api/faculty-workload');if(!node.isConnected)return;
 node.innerHTML=table(['Faculty','Lecture hours','Practical hours','Tutorial hours','Supervised project hours','Total / limit','Available hours',''],rows.map(t=>cells([esc(t.name),t.lecture,t.lab,t.tutorial,t.project,`${t.total} / ${t.weekly_limit}${t.auto_workload?' (automatic)':''}`,t.available_hours,`<button class="button small" data-action="edit-faculty" data-id="${esc(t.id)}">Edit preferences</button>`])))+'<p class="inline-help">These are assigned physical teaching hours, not student-hours. Actual scheduled hours are shown in Analytics. Automatic limits prevent artificial cap failures; hours beyond real faculty availability still require a valid correction.</p>';
 }catch(e){if(node.isConnected)node.textContent=e.message;}
}
const renderBeforePreferences=render;
render=function(){renderBeforePreferences();loadFacultyDetails();
 const g=state.generation;if(state.page==='timetables'&&g?.result?.preferences){
 const p=g.result.preferences;const div=document.createElement('div');div.className='info-banner';div.textContent=`Room/time preferences: ${p.unmet_preferences.length} session(s) used an alternative preferred option. Required choices remain enforced.`;
 if(p.unmet_preferences.length){const details=document.createElement('details');details.innerHTML='<summary>View sessions using alternatives</summary><ul>'+p.unmet_preferences.map(e=>{const o=g.config.offerings.find(o=>o.id===e.offering_id),t=g.config.teachers.find(t=>t.id===o?.teacher_id),s=g.config.subjects.find(s=>s.id===o?.subject_id),r=g.config.rooms.find(r=>r.id===e.room_id);return `<li>${esc(t?.name||'')} · ${esc(s?.name||e.offering_id)} · ${esc(e.day)} ${esc(e.time)} · ${esc(r?.name||'No room')}</li>`;}).join('')+'</ul>';div.append(details);}
 document.getElementById('horizontal-timetable')?.before(div);
 }
};
const actionBeforePreferences=action;
action=async function(name,node){if(name!=='reset-data')return actionBeforePreferences(name,node);
 openModal('Delete all data','Start a new semester',`<form id="modal-form"><div class="modal-body"><p>This clears faculty, subjects, assignments, divisions, batches, rooms and elective sets. College timings are retained. A backup is saved automatically in data/backups.</p><p><a href="/api/config.json" class="button">Download academic backup first</a></p><label><input type="checkbox" name="delete_history"> Also delete saved timetable history</label><label class="field">Type DELETE ALL DATA<input name="confirmation" required autocomplete="off"></label></div><div class="form-error" id="form-error"></div><div class="form-actions">${btn('Cancel','close-modal')}<button type="submit" class="button danger">Delete all data</button></div></form>`,async form=>{
 if(form.elements.confirmation.value!=='DELETE ALL DATA')throw Error('Type DELETE ALL DATA exactly to confirm.');
 const result=await api('/api/reset-academic-data',jsonOptions('POST',{revision:state.revision,confirmation:'DELETE ALL DATA',delete_history:form.elements.delete_history.checked}));
 state.config=result.configuration;state.revision=result.revision;state.history=await api('/api/generations');state.generation=null;state.department='';state.target='';state.batch='';state.search='';state.tab='teachers';closeModal();render();toast('Academic data cleared. Backup: '+result.backup);
 });
};
