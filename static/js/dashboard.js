/* ==========================================================================
   Dashboard (Inicio) - carga tarjetas, ultimas ventas y alertas
   ========================================================================== */

(() => {
  const { $, get, money, number, formatDate, escapeHtml, categoryIcon } = Shevelle;

  /* ------------------------------------------------- Tarjetas de resumen */
  const CARD_STYLES = ['', 'mint', 'gold', 'rose'];

  function renderCards(cards, summary) {
    const box = $('#dashboardCards');
    if (!box) return;

    const order = ['sales_today', 'products', 'low_stock', 'profits'];
    box.innerHTML = order.map((key, index) => {
      const card = cards[key];
      if (!card) return '';
      const foot = {
        sales_today: `${number(card.count)} venta(s) · ${number(card.units)} unidad(es)`,
        products:    `${number(card.units)} unidades en inventario`,
        low_stock:   card.value === 0 ? 'Todo bien 👍' : 'Requieren reposición',
        profits:     `Hoy: ${money(summary.day.profit)}`
      }[key] || '';

      return `
        <div class="stat ${CARD_STYLES[index] || ''}">
          <div class="stat-top">
            <span class="stat-label">${escapeHtml(card.label)}</span>
            <span class="stat-icon">${card.icon}</span>
          </div>
          <div class="stat-value">${escapeHtml(card.formatted)}</div>
          <div class="stat-foot">${escapeHtml(foot)}</div>
        </div>`;
    }).join('');
  }

  /* --------------------------------------------------- Ultimas ventas */
  function renderRecentSales(sales) {
    const box = $('#recentSales');
    if (!box) return;

    if (!sales.length) {
      box.innerHTML = `
        <div class="empty">
          <div class="big">🛍️</div>
          <h3>Aún no tienes ventas registradas</h3>
          <p>Registra tu primera venta y aquí aparecerá el historial con sus ganancias.</p>
          <a href="/ventas" class="btn btn-primary btn-sm">🛒 Registrar una venta</a>
        </div>`;
      return;
    }

    box.innerHTML = sales.map((sale) => `
      <div class="sale-row">
        <div class="sale-ico">${categoryIcon(sale.category)}</div>
        <div class="sale-info">
          <strong>${escapeHtml(sale.product_name)}</strong>
          <small>${number(sale.quantity)} unidad(es) · ${escapeHtml(formatDate(sale.created_at))}</small>
        </div>
        <div class="sale-nums">
          <div class="total">${money(sale.total)}</div>
          <div class="profit">+${money(sale.profit)} ganancia</div>
        </div>
      </div>`).join('');
  }

  /* --------------------------------------------- Alertas de inventario */
  function renderAlerts(alerts, threshold) {
    const box = $('#stockAlerts');
    if (!box) return;

    $('#alertThreshold').textContent = `Productos con ${threshold} unidades o menos`;

    if (!alerts.length) {
      box.innerHTML = `
        <div class="notice ok">
          <span>🎉</span>
          <div><strong>Todo en orden.</strong> Ningún producto está en inventario bajo.</div>
        </div>`;
      return;
    }

    box.innerHTML = alerts.map((alert) => `
      <div class="alert-item ${alert.level === 'danger' ? 'danger' : ''}">
        <span class="alert-ico">${alert.level === 'danger' ? '🔴' : '⚠️'}</span>
        <span>${escapeHtml(alert.text)}</span>
        <span class="spacer"></span>
        <a class="btn btn-ghost btn-sm" href="/productos?search=${encodeURIComponent(alert.text.split(':')[0].replace('⚠️', '').trim())}">Ver</a>
      </div>`).join('');
  }

  /* ------------------------------------------------- Top productos */
  function renderTopProducts(list) {
    const box = $('#topProducts');
    if (!box) return;

    if (!list.length) {
      box.innerHTML = `
        <div class="empty">
          <div class="big">🏆</div>
          <h3>Todavía no hay datos de ventas</h3>
          <p>Aquí verás qué productos se venden más, según tus registros reales.</p>
        </div>`;
      return;
    }

    const max = Math.max(...list.map((item) => item.units)) || 1;
    box.innerHTML = list.map((item) => `
      <div class="hbar">
        <div class="hbar-top">
          <strong>${escapeHtml(item.name)}</strong>
          <span class="num">${number(item.units)} u. · ${money(item.profit)}</span>
        </div>
        <div class="hbar-track">
          <div class="hbar-fill" style="width:${(item.units / max) * 100}%"></div>
        </div>
      </div>`).join('');
  }

  /* ------------------------------------------------------------- Carga */
  async function load() {
    try {
      const data = await get('/api/dashboard');
      Shevelle.currency = data.business.currency;

      renderCards(data.cards, data.summary);
      renderRecentSales(data.recent_sales);
      renderAlerts(data.alerts, data.threshold);
      renderTopProducts(data.top_products);

      $('#heroSales').textContent    = data.cards.sales_today.count;
      $('#heroProfit').textContent   = money(data.summary.day.profit);
      $('#heroProducts').textContent = data.cards.products.value;
      $('#heroAlerts').textContent   = data.cards.low_stock.value;
    } catch (error) {
      Shevelle.toast(error.message, 'error', 'No se pudo cargar el panel');
      $('#recentSales').innerHTML = `<div class="notice err"><span>❌</span><div>${escapeHtml(error.message)}</div></div>`;
    }
  }

  document.addEventListener('DOMContentLoaded', load);
  window.addEventListener('product:changed', load);
})();
