/* ==========================================================================
   Recomendador "Encuentra tu producto" - cuestionario de 2 pasos
   ========================================================================== */

(() => {
  const wizard = $('#wizard');
  if (!wizard) return;

  const { $, post, money, escapeHtml, toast } = Shevelle;
  const answers = {};

  function showStep(index) {
    wizard.querySelectorAll('.wizard-step').forEach((step) => {
      step.classList.toggle('active', Number(step.dataset.step) === index);
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  /* ------------------------------------------------ Render de resultado */
  function renderResult(data) {
    const grid = $('#recoGrid');

    if (!data.items.length) {
      grid.innerHTML = `
        <div class="card" style="grid-column:1/-1">
          <div class="empty">
            <div class="big">📦</div>
            <h3>No hay productos para recomendar</h3>
            <p>${escapeHtml(data.message || 'Registra productos con existencias primero.')}</p>
            <a href="/productos" class="btn btn-primary btn-sm">Ir a Productos</a>
          </div>
        </div>`;
      return;
    }

    $('#recoSubtitle').textContent =
      `Para «${data.need_label}» con estilo «${data.style_label}» — ${data.items.length} sugerencia(s) de tu inventario`;

    grid.innerHTML = data.items.map((item) => `
      <div class="reco-card">
        <div class="reco-img">
          ${item.image
            ? `<img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.name)}">`
            : Shevelle.categoryIcon(item.category)}
          <span class="reco-match">${item.match}% match</span>
        </div>
        <div class="reco-body">
          <span class="tag">${escapeHtml(item.category)}</span>
          <h3 style="margin-top:8px">${escapeHtml(item.name)}</h3>
          <p class="why">${escapeHtml(item.why)}</p>
          <div class="reco-foot">
            <div>
              <div class="product-price">${money(item.sale_price)}</div>
              <div class="product-cost">${item.stock} disponibles</div>
            </div>
            <button class="btn btn-soft btn-sm" data-reco="${item.id}">💬 Pedir info</button>
          </div>
        </div>
      </div>`).join('');
  }

  async function getRecommendation() {
    showStep(2);
    $('#recoGrid').innerHTML = `
      <div class="skeleton" style="height:290px"></div>
      <div class="skeleton" style="height:290px"></div>
      <div class="skeleton" style="height:290px"></div>`;

    try {
      const data = await post('/api/ai/recommend', { need: answers.necesidad, style: answers.estilo });
      renderResult(data);
    } catch (error) {
      $('#recoGrid').innerHTML = `
        <div class="card" style="grid-column:1/-1">
          <div class="notice err"><span>❌</span><div>${escapeHtml(error.message)}</div></div>
        </div>`;
      toast(error.message, 'error');
    }
  }

  /* --------------------------------------------------------- Eventos */
  wizard.addEventListener('click', (event) => {
    const option = event.target.closest('.option-card');
    if (!option) return;

    const step = option.dataset.step;
    const value = option.dataset.value;

    wizard.querySelectorAll(`.option-card[data-step="${step}"]`)
            .forEach((card) => card.classList.remove('active'));
    option.classList.add('active');
    answers[step] = value;

    setTimeout(() => {
      if (step === '0') showStep(1);
      else getRecommendation();
    }, 260);
  });

  wizard.addEventListener('click', (event) => {
    const button = event.target.closest('[data-reco]');
    if (!button) return;
    toast('Puedes copiar este texto para responderle a tu clienta por WhatsApp.', 'info',
          '💡 Consejo de venta');
  });

  $('#restartWizard')?.addEventListener('click', () => {
    delete answers.necesidad;
    delete answers.estilo;
    wizard.querySelectorAll('.option-card').forEach((card) => card.classList.remove('active'));
    showStep(0);
  });
})();
