/* ==========================================================================
   Asistente IA - interfaz de chat
   ========================================================================== */

(() => {
  const box = $('#chatMessages');
  if (!box) return;

  const { $, post, get, escapeHtml, number, toast } = Shevelle;
  const history = [];
  let sending = false;

  /* ------------------------------------------------ Pintar un mensaje */
  function addMessage(role, text, meta = '') {
    const element = document.createElement('div');
    element.className = `msg ${role === 'user' ? 'user' : 'ai'}`;
    element.innerHTML = `
      <div class="msg-avatar">${role === 'user' ? '👤' : '🦋'}</div>
      <div>
        <div class="msg-bubble">${escapeHtml(text)}</div>
        ${meta ? `<div class="msg-meta">${escapeHtml(meta)}</div>` : ''}
      </div>`;
    box.appendChild(element);
    box.scrollTop = box.scrollHeight;
    return element;
  }

  function showTyping() {
    const element = document.createElement('div');
    element.className = 'msg ai';
    element.id = 'typingIndicator';
    element.innerHTML = `
      <div class="msg-avatar">🦋</div>
      <div class="msg-bubble"><div class="typing"><span></span><span></span><span></span></div></div>`;
    box.appendChild(element);
    box.scrollTop = box.scrollHeight;
  }

  const removeTyping = () => document.getElementById('typingIndicator')?.remove();

  /* ----------------------------------------------------- Mensaje inicial */
  function welcome() {
    addMessage('ai',
      '¡Hola! 🦋 Soy tu asistente de Shevelle AI.\n\n' +
      'Puedo ayudarte con:\n' +
      '• **Ventas** — ideas para vender más y promociones\n' +
      '• **Contenido** — qué publicar hoy en Instagram o TikTok\n' +
      '• **Clientes** — respuestas a preguntas frecuentes\n' +
      '• **Negocio** — análisis de tus ventas e inventario\n\n' +
      'Inténtalo: pregúntame "¿Qué productos tengo disponibles?" o "¿Cuánto estoy ganando?".');
  }

  /* --------------------------------------------------------- Enviar */
  async function send(text) {
    const message = (text ?? '').trim();
    if (!message || sending) return;

    sending = true;
    addMessage('user', message);
    $('#chatInput').value = '';
    $('#chatInput').style.height = 'auto';
    showTyping();

    try {
      const result = await post('/api/ai/chat', { message, history: history.slice(-8) });

      removeTyping();
      const meta = result.source === 'api'
        ? `IA · ${result.mode}`
        : 'Datos reales de tu base de datos';
      addMessage('ai', result.reply, meta);

      history.push({ role: 'user', content: message });
      history.push({ role: 'assistant', content: result.reply });

      // Si la IA no esta configurada, lo avisamos una sola vez por bloque
      if (result.notice && !window.__noticeShown) {
        window.__noticeShown = true;
        addMessage('ai', '⚙️ ' + result.notice, 'Aviso del sistema');
      }
    } catch (error) {
      removeTyping();
      addMessage('ai', '😕 No pude responder: ' + error.message);
    } finally {
      sending = false;
      $('#chatSend').disabled = false;
    }
  }

  /* -------------------------------------------------------- Contexto */
  async function loadContext() {
    try {
      const status = await get('/api/ai/status');
      $('#ctxMode').textContent = status.ai_configured ? 'IA conectada' : 'Modo demostración';

      if (status.ai_configured) {
        $('#chatModeLabel').textContent = 'Conectado a la IA';
      }
    } catch (error) { /* no es critico */ }

    try {
      const health = await get('/api/health');
      $('#ctxProducts').textContent = number(health.products);
      $('#ctxSales').textContent    = number(health.sales);
    } catch (error) { /* no es critico */ }
  }

  /* --------------------------------------------------------- Eventos */
  $('#chatSend')?.addEventListener('click', () => send($('#chatInput').value));

  $('#chatInput')?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      send(event.target.value);
    }
  });

  $('#chatInput')?.addEventListener('input', (event) => {
    event.target.style.height = 'auto';
    event.target.style.height = Math.min(event.target.scrollHeight, 130) + 'px';
  });

  // Botones de sugerencias
  document.addEventListener('click', (event) => {
    const button = event.target.closest('[data-question]');
    if (!button) return;
    send(button.dataset.question);
  });

  document.addEventListener('DOMContentLoaded', () => {
    welcome();
    loadContext();
  });
})();
