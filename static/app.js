async function fetchTasks(){
  const res = await fetch('/api/tasks');
  return await res.json();
}

function createColumn(title, id){
  const el = document.createElement('div'); el.className='column'; el.id=id;
  const h = document.createElement('h3'); h.innerHTML=`<span>${title}</span> <span class="count">0</span>`; el.appendChild(h);
  const list = document.createElement('div'); list.className='list'; el.appendChild(list);
  return el;
}

function makeCard(t){
  const c=document.createElement('div'); c.className='card'; c.dataset.id=t.id;
  const title = document.createElement('div'); title.className='title'; title.textContent = t.title; c.appendChild(title);
  const meta = document.createElement('div'); meta.className='meta'; meta.textContent = `#${t.id}`; c.appendChild(meta);
  c.addEventListener('click', ()=> openModal(t.id));
  return c;
}

function render(tasks){
  const board = document.getElementById('board'); board.innerHTML='';
  const cols = {
    backlog: createColumn('Backlog','col-backlog'),
    todo: createColumn('To-Do','col-todo'),
    in_progress: createColumn('In-Progress','col-inprogress'),
    done: createColumn('Done','col-done')
  }
  for(const k in cols) board.appendChild(cols[k]);
  tasks.forEach(t=>{
    const list = cols[t.status || 'backlog'].querySelector('.list');
    const card = makeCard(t);
    list.appendChild(card);
  });
  // update counts
  Object.values(cols).forEach(col=>{ const list=col.querySelector('.list'); col.querySelector('h3 .count').textContent = list.children.length; });

  // initialize Sortable for each list
  Object.values(cols).forEach(col=>{
    Sortable.create(col.querySelector('.list'),{
      group: 'kanban',
      animation: 150,
      onEnd: async (evt)=>{
        const id = evt.item.dataset.id;
        let status='backlog';
        if(col.id==='col-todo') status='todo';
        if(col.id==='col-inprogress') status='in_progress';
        if(col.id==='col-done') status='done';
        await fetch(`/api/tasks/${id}`, {method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({status})});
        load();
      }
    });
  });
}

async function openModal(id){
  const res = await fetch(`/api/tasks/${id}`);
  const data = await res.json();
  document.getElementById('modal-title').textContent = `${data.title} (#${data.id})`;
  document.getElementById('modal-desc').textContent = data.description || '';
  const attachEl = document.getElementById('modal-attachments'); attachEl.innerHTML = '';
  data.attachments.forEach(a=>{ const link = document.createElement('a'); link.href = `/uploads/${a.path.split('/').pop()}`; link.textContent = a.filename; link.target='_blank'; attachEl.appendChild(link); attachEl.appendChild(document.createElement('br')); });
  document.getElementById('modal').style.display='flex';
  // wire actions
  document.getElementById('move-todo').onclick = ()=> updateStatus(id,'todo');
  document.getElementById('move-inprogress').onclick = ()=> updateStatus(id,'in_progress');
  document.getElementById('move-done').onclick = ()=> updateStatus(id,'done');
}

async function updateStatus(id,status){
  await fetch(`/api/tasks/${id}`, {method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({status})});
  document.getElementById('modal').style.display='none';
  load();
}

function setupUI(){
  document.getElementById('new-task-btn').addEventListener('click', ()=>{ document.getElementById('new-task-form').style.display='block'; });
  document.getElementById('cancel-create').addEventListener('click', ()=>{ document.getElementById('new-task-form').style.display='none'; });
  document.getElementById('modal-close').addEventListener('click', ()=>{ document.getElementById('modal').style.display='none'; });
  document.getElementById('create').addEventListener('click', async ()=>{
    const title=document.getElementById('title').value;
    const desc=document.getElementById('desc').value;
    if(!title) return alert('title required');
    await fetch('/api/tasks', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({title,description:desc})});
    document.getElementById('title').value=''; document.getElementById('desc').value='';
    document.getElementById('new-task-form').style.display='none';
    load();
  });
}

async function load(){
  const tasks = await fetchTasks(); render(tasks);
}

setupUI();
load();
