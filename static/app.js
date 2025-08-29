const byId = (id) => document.getElementById(id);
const chatBox = byId('chat');
const input = byId('input');
const sendBtn = byId('send');
const historyBtn = byId('btn-history');
const exportBtn = byId('btn-export');
const timelineBtn = byId('btn-timeline');
const fileInput = byId('file-input');

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    method: opts.method || 'GET',
    headers: opts.form ? undefined : { 'Content-Type': 'application/json' },
    body: opts.form ? opts.body : (opts.body ? JSON.stringify(opts.body) : undefined),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

function renderMessage({ who, text, sources, chatId, timeMs }) {
  const bubble = el('div', `bubble ${who}`);
  const meta = el('div', 'meta');
  meta.textContent = who === 'user' ? 'You' : 'Tutor';
  bubble.appendChild(meta);
  const body = el('div', 'text');
  body.textContent = text;
  bubble.appendChild(body);
  if (sources && sources.length) {
    const s = el('div', 'sources');
    s.innerHTML = '<b>Sources</b><br>' + sources.map(src => `${src.title} (${src.section})`).join('<br>');
    bubble.appendChild(s);
  }
  if (who === 'bot') {
    const fb = el('div', 'feedback');
    fb.appendChild(el('span', 'time', `${timeMs} ms`));
    const up = el('div', 'thumb up', '👍');
    const down = el('div', 'thumb down', '👎');
    up.title = 'Helpful';
    down.title = 'Not helpful';
    up.onclick = () => sendFeedback(chatId, 1);
    down.onclick = () => sendFeedback(chatId, -1);
    fb.appendChild(up);
    fb.appendChild(down);
    bubble.appendChild(fb);
  }
  chatBox.appendChild(bubble);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendFeedback(chatId, rating) {
  try {
    await api('/api/feedback', { method: 'POST', body: { chat_id: chatId, rating } });
  } catch (e) {
    console.error('feedback failed', e);
  }
  loadMetrics();
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  renderMessage({ who: 'user', text });
  input.value = '';
  input.disabled = true;
  sendBtn.disabled = true;
  try {
    const data = await api('/api/chat', { method: 'POST', body: { message: text } });
    renderMessage({ who: 'bot', text: data.answer, sources: data.sources, chatId: data.chat_id, timeMs: data.response_time_ms });
    await loadHistory();
    await loadMetrics();
  } catch (e) {
    renderMessage({ who: 'bot', text: 'Sorry, something went wrong. Please try again.' });
  } finally {
    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

async function listUploads() {
  try {
    const data = await api('/api/uploads');
    const ul = byId('uploads-list');
    ul.innerHTML = '';
    for (const u of data.uploads) {
      const li = el('li');
      li.innerHTML = `<div>${u.filename}</div><small>${Math.round((u.size||0)/1024)} KB • ${new Date(u.created_at).toLocaleString()}</small>`;
      ul.appendChild(li);
    }
  } catch (e) {
    console.error('uploads list failed', e);
  }
}

async function uploadPdf(file) {
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await api('/api/upload_pdf', { method: 'POST', body: form, form: true });
    renderMessage({ who: 'bot', text: 'PDF uploaded and indexed successfully.' });
    await listUploads();
  } catch (e) {
    renderMessage({ who: 'bot', text: 'Upload failed. Please try a different PDF.' });
  }
}

async function loadHistory() {
  try {
    const data = await api('/api/history');
    const list = byId('history-list');
    list.innerHTML = '';
    for (const item of data.history) {
      const li = el('li');
      const q = item.user_message.length > 90 ? item.user_message.slice(0, 90) + '…' : item.user_message;
      li.innerHTML = `<div>${q}</div><small>${new Date(item.created_at).toLocaleString()}</small>`;
      li.onclick = () => {
        renderMessage({ who: 'user', text: item.user_message });
        renderMessage({ who: 'bot', text: item.bot_message, sources: item.sources, chatId: item.id, timeMs: item.response_time_ms });
      };
      list.appendChild(li);
    }
  } catch (e) {
    console.error('history load failed', e);
  }
}

async function exportHistory() {
  try {
    const data = await api('/api/history?limit=1000');
    const blob = new Blob([JSON.stringify(data.history, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = el('a');
    a.href = url;
    a.download = `constitution_tutor_history_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    console.error('export failed', e);
  }
}

async function loadMetrics() {
  try {
    const m = await api('/api/metrics');
    byId('m-total').textContent = m.total_chats;
    byId('m-avg').textContent = `${m.avg_response_time_ms} ms`;
    byId('m-helpful').textContent = `${Math.round(m.helpful_rate * 100)}%`;
    const ul = byId('m-top');
    ul.innerHTML = '';
    for (const d of m.top_docs) {
      const li = el('li');
      li.textContent = `${d.title} – ${d.count}`;
      ul.appendChild(li);
    }
  } catch (e) {
    // ignore
  }
}

async function showTimeline() {
  try {
    const t = await api('/api/constitution_history');
    renderMessage({ who: 'bot', text: `${t.title}\n\n${t.content}` });
  } catch (e) {
    renderMessage({ who: 'bot', text: 'Timeline not available right now.' });
  }
}

sendBtn.addEventListener('click', sendMessage);
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
historyBtn.addEventListener('click', loadHistory);
exportBtn.addEventListener('click', exportHistory);
timelineBtn.addEventListener('click', showTimeline);
fileInput.addEventListener('change', (e) => {
  const f = e.target.files && e.target.files[0];
  if (f) uploadPdf(f);
});

loadHistory();
loadMetrics();
listUploads();
input.focus();

