/* ==========================================================================
   Modulo Configuracion - ajustes del negocio y estado de la IA
   ========================================================================== */

(() => {
  const form = $('#settingsForm');
  if (!form) return;

  const { $, get, put, money, number, escapeHtml, toast, confirmAction } = Shevelle;

  /* --------------------------------------------------- Cargar ajustes */
  async function load() {
    try {
      const data = await get('/api/settings');
      const settings = data.settings;

      $('#setBusinessName').value = settings.business_name || '';
      $('#setOwner').value        = settings.business_owner || '';
      $('#setCurrency').value     = settings.currency || 'RD$';
      $('#setThreshold').value    = settings.low_stock_threshold ?? 3;
      $('#setAiEnabled').checked  = String(settings.ai_enabled) !== 'false';

      renderAiStatus(data);
      $('#aboutMode').textContent = data.ai_mode;
    } catch (error) {
      toast(error.message, 'error', 'No se pudo cargar la configuración');
    }
  }

  /* ------------------------------------------------- Estado de la IA */
  function renderAiStatus(data) {
    const box = $('#aiStatusBox');
    if (data.ai_configured) {
      box.innerHTML = `
        <div class="notice ok">
          <span>✅</span>
          <div>
            <strong>Inteligencia artificial conectada.</strong><br>
            El asistente usa el modelo <code>${escapeHtml(data.ai_mode)}</code> y los datos reales de tu base de datos.
          </div>
        </div>`;
    } else {
      box.innerHTML = `
        <div class="notice">
          <span>⚙️</span>
          <div>
            <strong>La IA todavía no está configurada.</strong><br>
            La aplicación funciona igual: el asistente responde con los datos reales
            de tu base de datos usando plantillas inteligentes.
          </div>
        </div>`;
    }
  }

  /* ------------------------------------------------------ Guardar */
  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = '⏳ Guardando...';

    try {
      const result = await put('/api/settings', {
        business_name: $('#setBusinessName').value.trim() || 'Shevelle Beauty',
        business_owner: $('#setOwner').value.trim(),
        currency: $('#setCurrency').value.trim() || 'RD$',
        low_stock_threshold: $('#setThreshold').value,
        ai_enabled: $('#setAiEnabled').checked ? 'true' : 'false'
      });

      Shevelle.currency = result.settings.currency;
      toast(result.message, 'ok');
      $('#aboutCurrency').textContent = result.settings.currency;
      $('#demoCount').textContent = `${number(result.settings.low_stock_threshold)} unidades = alerta`;
    } catch (error) {
      toast(error.message, 'error', 'No se pudo guardar');
    } finally {
      button.disabled = false;
      button.textContent = '💾 Guardar configuración';
    }
  });

  /* ------------------------------------------- Datos de demostracion */
  async function loadDemoCount() {
    try {
      const data = await get('/api/products');
      $('#demoCount').textContent = `${number(data.count)} productos en total`;
    } catch (error) { /* no es critico */ }
  }

  $('#resetDemoBtn')?.addEventListener('click', async () => {
    const ok = await confirmAction(
      'Se eliminarán TODOS los productos y TODAS las ventas para restaurar los datos de ejemplo. Esta acción no se puede deshacer.',
      '¿Restaurar datos de demostración?'
    );
    if (!ok) return;

    const button = $('#resetDemoBtn');
    button.disabled = true;
    const original = button.textContent;
    button.textContent = '⏳ Restaurando...';

    try {
      const result = await Shevelle.post('/api/settings/reset-demo', {});
      const d = result.data || {};
      toast(
        `${result.message} ${Shevelle.number(d.products || 0)} productos y ${Shevelle.number(d.sales || 0)} ventas de ejemplo.`,
        'ok', '🔄 Datos restaurados'
      );
      await load();
      await loadDemoCount();
    } catch (error) {
      toast(error.message, 'error', 'No se pudieron restaurar los datos');
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  });

  /* ------------------------------------------------------------ Inicio */
  document.addEventListener('DOMContentLoaded', () => { load(); loadDemoCount(); });
})();
