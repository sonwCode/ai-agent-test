async function api(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  const type = res.headers.get('content-type') || '';
  if (type.includes('application/json')) return res.json();
  return res.text();
}

function toast(msg) {
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2600);
}

async function refreshHealth() {
  const data = await api('/api/health');
  document.getElementById('runtimeStatus').textContent = `${data.status} · ${data.llm_provider}`;
}

async function refreshDashboard() {
  const d = await api('/api/dashboard');
  document.getElementById('mTotalTasks').textContent = d.total_tasks;
  document.getElementById('mCompleted').textContent = d.completed_tasks;
  document.getElementById('mDocs').textContent = d.total_docs;
  document.getElementById('mScore').textContent = d.avg_quality_score;
}

async function refreshKnowledge() {
  const list = await api('/api/knowledge');
  const box = document.getElementById('knowledgeList');
  box.innerHTML = list.map(d => `
    <div class="item">
      <div class="item-title">${escapeHtml(d.title)} <span class="badge">${d.chunk_count} chunks</span></div>
      <div class="item-meta">${escapeHtml(d.filename)} · ${d.created_at}</div>
    </div>
  `).join('') || '<div class="item">暂无知识库资料</div>';
}

async function refreshTasks() {
  const list = await api('/api/tasks');
  const box = document.getElementById('taskList');
  box.innerHTML = list.map(t => `
    <div class="item" onclick="loadTask(${t.id})">
      <div class="item-title">#${t.id} ${escapeHtml(t.title)} <span class="badge">${t.status}</span></div>
      <div class="item-meta">质量分 ${t.quality_score || 0} · ${t.created_at}</div>
    </div>
  `).join('') || '<div class="item">暂无任务</div>';
}

async function refreshAll() {
  try {
    await Promise.all([refreshHealth(), refreshDashboard(), refreshKnowledge(), refreshTasks()]);
  } catch (e) {
    toast(e.message);
  }
}

async function uploadFile() {
  const input = document.getElementById('fileInput');
  if (!input.files.length) return toast('请先选择文件');
  const fd = new FormData();
  fd.append('file', input.files[0]);
  try {
    const data = await api('/api/knowledge/upload', { method: 'POST', body: fd });
    toast(data.message);
    input.value = '';
    await refreshAll();
  } catch (e) {
    toast('上传失败：' + e.message);
  }
}

async function runTask() {
  const payload = {
    title: document.getElementById('title').value,
    task_type: document.getElementById('taskType').value,
    goal: document.getElementById('goal').value,
    context: document.getElementById('context').value,
    deliverable: document.getElementById('deliverable').value,
  };
  try {
    toast('Agent 工作流运行中...');
    const task = await api('/api/tasks/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    toast('任务完成');
    await refreshAll();
    await loadTask(task.id);
  } catch (e) {
    toast('运行失败：' + e.message);
  }
}

async function loadTask(id) {
  const t = await api(`/api/tasks/${id}`);
  const detail = {
    id: t.id,
    title: t.title,
    status: t.status,
    quality_score: t.quality_score,
    result_summary: t.result_summary,
    artifacts: t.artifacts,
    steps: t.steps.map(s => ({
      agent_name: s.agent_name,
      step_name: s.step_name,
      status: s.status,
      output: tryParse(s.output_text),
    })),
    audit_logs: t.audit_logs,
  };
  let text = JSON.stringify(detail, null, 2);
  if (t.artifacts && t.artifacts.length) {
    const art = await api(`/api/artifacts/${t.artifacts[0].id}`);
    text += `\n\n================ 生成物预览 ================\n\n${art}`;
  }
  document.getElementById('taskDetail').textContent = text;
}

function tryParse(text) {
  try { return JSON.parse(text); } catch { return text; }
}

function escapeHtml(str) {
  return String(str || '').replace(/[&<>"]/g, s => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[s]));
}

refreshAll();
