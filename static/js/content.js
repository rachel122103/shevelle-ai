/* ==========================================================================
   Generador de contenido para redes sociales
   ========================================================================== */

(() => {
  const form = $('#contentForm');
  if (!form) return;

  const { $, get, post, money, escapeHtml, toast } = Shevelle;
  const selection = { platform: 'Instagram', content_type: 'Publicacion', tone: 'Elegante' };
  let lastResult = null;

  /* ----------------------------------------------- Chips seleccionables */
  function initChips(containerId, key) {
    const container = $(containerId);
    if (!container) return;

    container.addEventListener('click', (event) => {
      const chip = event.target.closest('.chip');
      if (!chip) return;
      container.querySelectorAll('.chip').forEach((c) => c.classList.remove('active'));
      chip.classList.add('active');
      selection[key] = chip.dataset.value;
    });
  }

  /* ------------------------------------------------- Cargar productos */
  async function loadProducts() {
    const select = $('#contentProduct');
    try {
      const data = await get('/api/products');
      if (!data.products.length) {
        select.innerHTML = '<option value="">No hay productos registrados</option>';
        $('#contentProductHint').innerHTML =
          '<a href="/productos">Agrega productos</a> para poder generar contenido sobre ellos.';
        return;
      }

      select.innerHTML = '<option value="">Selecciona un producto...</option>' +
        data.products.map((p) => `
          <option value="${p.id}">
            ${escapeHtml(p.name)} — ${escapeHtml(p.category)} — ${money(p.sale_price)}${p.stock <= 0 ? ' (agotado)' : ''}
          </option>`).join('');

      select.addEventListener('change', () => {
        const product = data.products.find((p) => String(p.id) === select.value);
        if (!product) { $('#contentProductHint').textContent = 'Selecciona un producto de la lista.'; return; }
        $('#contentProductHint').innerHTML = product.stock <= 0
          ? `⚠️ <b>${escapeHtml(product.name)}</b> está agotado. El contenido avisará que quedan últimas unidades.`
          : `<b>${escapeHtml(product.name)}</b> · ${product.stock} unidades · precio ${money(product.sale_price)}`;
      });
    } catch (error) {
      select.innerHTML = '<option value="">Error al cargar productos</option>';
      toast(error.message, 'error');
    }
  }

  /* ------------------------------------------------------ Generar */
  function renderResult(result) {
    lastResult = result;
    $('#resultActions').style.display = 'flex';
    $('#resultMeta').textContent =
      `${result.product} · ${result.platform} · ${result.content_type} · ${result.tone}`;

    $('#contentResult').innerHTML = `
      <div class="content-result">
        ${result.notice ? `<div class="notice" style="margin-bottom:16px"><span>⚙️</span><div>${escapeHtml(result.notice)}</div></div>` : ''}

        <div class="content-block">
          <h4>📝 Texto principal</h4>
          <p>${escapeHtml(result.texto)}</p>
        </div>

        <div class="content-block">
          <h4>📣 Llamado a la acción</h4>
          <p>${escapeHtml(result.llamado_accion)}</p>
        </div>

        <div class="content-block">
          <h4>#️⃣ Hashtags</h4>
          <div class="hashtags">
            ${result.hashtags.map((h) => `<span class="hashtag">${escapeHtml(h)}</span>`).join('')}
          </div>
        </div>
      </div>`;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const productId = $('#contentProduct').value;
    if (!productId) return toast('Selecciona un producto primero.', 'error');

    const button = $('#generateBtn');
    button.disabled = true;
    button.textContent = '⏳ Generando...';
    $('#contentResult').innerHTML = `
      <div class="skeleton" style="height:32px;margin-bottom:12px"></div>
      <div class="skeleton" style="height:90px;margin-bottom:12px"></div>
      <div class="skeleton" style="height:32px"></div>`;

    try {
      const result = await post('/api/ai/content', {
        product_id: Number(productId),
        platform: selection.platform,
        content_type: selection.content_type,
        tone: selection.tone
      });
      renderResult(result);
      toast('Contenido generado. ¡Ya puedes copiarlo!', 'ok');
    } catch (error) {
      $('#contentResult').innerHTML = `
        <div class="notice err"><span>❌</span><div>${escapeHtml(error.message)}</div></div>`;
      toast(error.message, 'error', 'No se pudo generar el contenido');
    } finally {
      button.disabled = false;
      button.textContent = '✨ Generar contenido';
    }
  });

  /* ------------------------------------------------------ Copiar texto */
  $('#copyBtn')?.addEventListener('click', async () => {
    if (!lastResult) return;

    const full = [
      lastResult.texto,
      '',
      lastResult.llamado_accion,
      '',
      lastResult.hashtags_text
    ].join('\n');

    try {
      await navigator.clipboard.writeText(full);
      toast('Texto copiado al portapapeles.', 'ok', '📋 Copiado');
    } catch (error) {
      // Alternativa para navegadores antiguos
      const area = document.createElement('textarea');
      area.value = full;
      area.style.position = 'fixed';
      area.style.opacity = '0';
      document.body.appendChild(area);
      area.select();
      try {
        document.execCommand('copy');
        toast('Texto copiado al portapapeles.', 'ok', '📋 Copiado');
      } catch (err) {
        toast('No se pudo copiar. Selecciona el texto y cópialo manualmente.', 'warn');
      }
      area.remove();
    }
  });

  $('#regenerateBtn')?.addEventListener('click', () => {
    if ($('#contentProduct').value) form.requestSubmit();
  });

  /* ------------------------------------------------------------- Inicio */
  document.addEventListener('DOMContentLoaded', () => {
    initChips('#platformChips', 'platform');
    initChips('#typeChips', 'content_type');
    initChips('#toneChips', 'tone');
    loadProducts();
  });
})();
