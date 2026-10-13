'use strict';
const API = 'http://127.0.0.1:8765';
const chat = document.querySelector('#chat');
const prompt = document.querySelector('#prompt');
const send = document.querySelector('#send');
const stop = document.querySelector('#stop');
let messages = [];
let controller;
function append(role, text) {
  const row = document.createElement('div');
  row.className = `message ${role}`;
  row.textContent = text;
  chat.append(row);
  row.scrollIntoView({block:'nearest'});
}
async function status() {
  const label = document.querySelector('#status');
  try {
    const response = await fetch(`${API}/api/status`, {signal:AbortSignal.timeout(5000)});
    const value = await response.json();
    label.textContent = value.ready ? `Local model ready · ${value.model}` : `Model not ready · ${value.model}`;
  } catch { label.textContent = 'Start the local AI service to ask questions. See the setup guide.'; }
}
document.querySelector('#form').addEventListener('submit', async event => {
  event.preventDefault();
  const text = prompt.value.trim();
  if (!text || controller) return;
  const pending = {role:'user', content:text};
  append('user', text);
  prompt.value = '';
  send.disabled = true;
  stop.disabled = false;
  controller = new AbortController();
  const timeout = setTimeout(() => controller?.abort(), 125000);
  try {
    const response = await fetch(`${API}/api/chat`, {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({messages:[...messages.slice(-18),pending]}), signal:controller.signal});
    const value = await response.json();
    if (!response.ok) throw new Error(value.error || 'Local assistant unavailable');
    if (typeof value.reply !== 'string') throw new Error('Invalid assistant response');
    messages.push(pending, {role:'assistant',content:value.reply});
    append('assistant', value.reply);
  } catch(error) { append('error', error.name === 'AbortError' ? 'Stopped waiting. The local model may finish its current request.' : error.message); }
  finally {clearTimeout(timeout);controller=null;send.disabled=false;stop.disabled=true;}
});
stop.addEventListener('click', () => controller?.abort());
document.querySelector('#clear').addEventListener('click', () => {if(controller)return;messages=[];chat.replaceChildren();});
document.querySelectorAll('[data-prompt]').forEach(button => button.addEventListener('click', () => {prompt.value=button.dataset.prompt;prompt.focus();}));
status();
