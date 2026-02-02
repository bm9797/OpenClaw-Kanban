async function fetchTasks(){
  const res = await fetch('/api/tasks');
  return await res.json();
}

function createColumn(title, id){
  const el = document.createElement('div'); el.className='column'; el.id=id;
  const h = document.createElement('h3'); h.textContent=title; el.appendChild(h);
  const list = document.createElement('div'); list.className='list'; el.appendChild(list);
  return el;
}

function render(tasks){
  const board = document.getElementById('board'); board.innerHTML='';
  const cols = {backlog: createColumn('Backlog','col-backlog'), todo:createColumn('To-Do','col-todo'), in_progress:createColumn('In-Progress','col-inprogress'), done:createColumn('Done','col-done')}
  for(const k in cols) board.appendChild(cols[k]);
  tasks.forEach(t=>{
    const c=document.createElement('div'); c.className='card'; c.textContent=t.title; c.dataset.id=t.id;
    const list = cols[t.status || 'backlog'].querySelector('.list'); list.appendChild(c);
    c.draggable=true;
    c.addEventListener('dragstart', e=>{ e.dataTransfer.setData('text/plain', t.id); });
  });
  // drag/drop
  Object.values(cols).forEach(col=>{
    const list=col.querySelector('.list');
    list.addEventListener('dragover', e=>{ e.preventDefault(); });
    list.addEventListener('drop', async e=>{
      e.preventDefault(); const id = e.dataTransfer.getData('text/plain');
      let status='backlog';
      if(col.id==='col-todo') status='todo';
      if(col.id==='col-inprogress') status='in_progress';
      if(col.id==='col-done') status='done';
      await fetch(`/api/tasks/${id}`, {method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({status})});
      load();
    });
  });
}

async function load(){
  const tasks = await fetchTasks(); render(tasks);
}

document.getElementById('create').addEventListener('click', async ()=>{
  const title=document.getElementById('title').value;
  const desc=document.getElementById('desc').value;
  if(!title) return alert('title required');
  await fetch('/api/tasks', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({title,description:desc})});
  document.getElementById('title').value=''; document.getElementById('desc').value='';
  load();
});

load();
