'use strict';
const horizontalCache=new Map();
function horizontalMarkup(layout){
 const positions=new Map(layout.cells.map(c=>[`${c.row}:${c.col}`,c]));
 const covered=new Set();
 layout.cells.forEach(c=>{for(let r=c.row;r<c.row+c.rowspan;r++)for(let col=c.col;col<c.col+c.colspan;col++)if(r!==c.row||col!==c.col)covered.add(`${r}:${col}`);});
 let html=`<div class="college-form-scroll"><div class="college-form"><div class="college-form-heading">${layout.headers.map((t,i)=>`<div class="heading-${i}">${esc(t)}</div>`).join('')}<div class="college-form-details">${layout.details.map(t=>`<span>${esc(t)}</span>`).join('')}</div></div><table class="horizontal-table" aria-label="${esc(layout.title)} weekly timetable"><thead><tr><th rowspan="2" scope="col">DAYS</th>${layout.columns.map((c,i)=>`<th scope="col" class="${c.break?'break-column':''}">${i+1}</th>`).join('')}</tr><tr>${layout.columns.map(c=>`<th class="time-heading">${esc(c.time)}</th>`).join('')}</tr></thead><tbody>`;
 for(let r=1;r<layout.row_count;r++){
  html+='<tr>';
  for(let col=0;col<=layout.columns.length;col++){
   if(covered.has(`${r}:${col}`))continue;
   const c=positions.get(`${r}:${col}`);if(!c)continue;
   const tag=c.kind==='day'?'th':'td';
   html+=`<${tag} ${tag==='th'?'scope="rowgroup"':''} rowspan="${c.rowspan}" colspan="${c.colspan}" class="horizontal-${esc(c.kind)}" title="${esc(c.detail)}">${esc(c.text).replaceAll('\n','<br>')}`;
   if(c.slot!==null&&c.slot!==undefined){const time=layout.columns[c.col-1]?.time||'';html+=`<button class="horizontal-free" data-action="horizontal-free" data-day="${c.day}" data-slot="${c.slot}" data-duration="${c.duration}" aria-label="Check free faculty and rooms for ${esc(layout.days[c.day].day)} ${esc(time)}" title="Check free faculty, classrooms and labs">ⓘ</button>`;}
   html+=`</${tag}>`;
  }
  html+='</tr>';
 }
 html+='</tbody></table>';
 html+=`<div class="horizontal-legends">${layout.legends.map(l=>`<section><h3>${esc(l.title)}</h3>${l.items.map(x=>`<div>${esc(x)}</div>`).join('')}</section>`).join('')}</div><div class="college-signatures">${layout.signatures.map(t=>`<div>${esc(t).replaceAll('\n','<br>')}</div>`).join('')}</div></div></div><p class="horizontal-note">Term, academic year and commencement date are left blank for completion. Signature and seal spaces are unsigned. Hover for session details; ⓘ shows free resources.</p>`;
 return html;
}
async function loadHorizontal(){
 const node=document.getElementById('horizontal-timetable');if(!node)return;
 const g=state.generation;const key=`${g.id}|${state.view}|${state.target}|${state.batch||''}`;
 node.dataset.layoutKey=key;
 try{
  if(!horizontalCache.has(key)){
   const query=new URLSearchParams({view:state.view,target:state.target});if(state.batch)query.set('batch',state.batch);
   const layouts=await api(`/api/generations/${g.id}/layout?${query}`);horizontalCache.set(key,layouts[0]);
  }
  if(node.isConnected&&node.dataset.layoutKey===key)node.innerHTML=horizontalMarkup(horizontalCache.get(key));
 }catch(error){if(node.isConnected)node.textContent='Unable to display timetable: '+error.message;}
}
const renderBeforeHorizontal=render;
render=function(){renderBeforeHorizontal();loadHorizontal();};
const actionBeforeHorizontal=action;
action=async function(name,node){if(name==='horizontal-free'){await showAvailability(Number(node.dataset.day),Number(node.dataset.slot),Number(node.dataset.duration));return;}return actionBeforeHorizontal(name,node);};
