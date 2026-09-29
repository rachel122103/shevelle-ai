/* ==========================================================================
   Modulo Estadisticas - graficos, top productos y valor del inventario
   ========================================================================== */

(() => {
  const { $, get, money, number, escapeHtml } = Shevelle;
  if (!$('#statsChart')) return;

  /* Colores usados en el grafico de categorias */
  const COLORS = ['#9B7EDE', '#C9A227', '#2E9E6B', '#D1466B', '#4C8FD4',
                  '#B79BEA', '#E4CD7B', '#7ED3A8', '#F09BB3', '#9A95A8'];

  /* ------------------------------------------------- Tarjetas resumen */
  function renderSummary(summary) {
    const set = (id, footId, value, foot) => {
      $(id).textContent = value;
      $(footId).textContent = foot;
    };

    set('#statSales', '#statSalesFoot', number(summary.all.sales), 'registradas en total');
    set('#statUnits', '#statUnitsFoot', number(summary.all.units), 'unidades vendidas');
    set('#statRevenue', '#statRevenueFoot', money(summary.all.revenue), 'ingresos acumulados');
    set('#statProfit', '#statProfitFoot', money(summary.all.profit), 'ganancia acumulada');
  }

  /* --------------------------------------------- Grafico de barras */
  function renderChart(series) {
    const max = Math.max(...series.map((d) => d.revenue), 1);

    $('#statsChart').innerHTML = `
      <div class="bars">
        ${series.map((day) => {
          const height = Math.max(2, (day.revenue / max) * 100);
          return `
            <div class="bar-col">
              <span class="bar-value">${day.revenue > 0 ? money(day.revenue).replace(/\.00$/, '') : ''}</span>
              <div class="bar-track" title="${escapeHtml(day.date)}: ${money(day.revenue)}">
                <div class="bar-fill" style="height:${height}%"></div>
              </div>
              <span class="bar-label">${escapeHtml(day.label)}</span>
            </div>`;
        }).join('')}
      </div>
      <p style="text-align:center;font-size:.75rem;color:var(--gris-tenue);margin-top:12px">
        Ingresos por día de los últimos 7 días
      </p>`;
  }

  /* ------------------------------------------ Grafico circular (CSS) */
  function renderDonut(categories) {
    const box = $('#categoryDonut');
    if (!categories.length) {
      box.innerHTML = `<div class="empty" style="width:100%">
        <p>Sin ventas por categoría todavía.</p></div>`;
      return;
    }

    const total = categories.reduce((sum, c) => sum + c.revenue, 0) || 1;
    let accumulated = 0;

    // Gradiente cónico construido con los datos REALES
    const stops = categories.map((category, index) => {
      const start = (accumulated / total) * 100;
      accumulated += category.revenue;
      const end = (accumulated / total) * 100;
      return `${COLORS[index % COLORS.length]} ${start.toFixed(1)}% ${end.toFixed(1)}%`;
    }).join(', ');

    box.innerHTML = `
      <div class="donut" style="background:conic-gradient(${stops})">
        <div class="donut-center">
          <div>
            <strong>${money(total).replace(/\.00$/, '')}</strong>
            <span>${categories.length} categoría(s)</span>
          </div>
        </div>
      </div>
      <div class="legend">
        ${categories.map((category, index) => `
          <div class="legend-item">
            <span class="legend-dot" style="background:${COLORS[index % COLORS.length]}"></span>
            <strong>${escapeHtml(category.category)}</strong>
            <span>${money(category.revenue)}</span>
          </div>`).join('')}
      </div>`;
  }

  /* ------------------------------------------------- Top productos */
  function renderTop(list) {
    const box = $('#statsTopProducts');
    if (!list.length) {
      box.innerHTML = `<div class="empty" style="padding:30px 10px">
        <p>Aún no hay productos vendidos.</p></div>`;
      return;
    }

    const max = Math.max(...list.map((item) => item.units)) || 1;
    box.innerHTML = list.map((item, index) => `
      <div class="hbar">
        <div class="hbar-top">
          <strong>${index + 1}. ${escapeHtml(item.name)}</strong>
          <span class="num">${number(item.units)} u.</span>
        </div>
        <div class="hbar-track">
          <div class="hbar-fill ${index % 2 ? 'gold' : ''}" style="width:${(item.units / max) * 100}%"></div>
        </div>
        <small style="color:var(--gris-tenue)">${money(item.revenue)} en ingresos · ${money(item.profit)} de ganancia</small>
      </div>`).join('');
  }

  /* ------------------------------------------- Valor del inventario */
  function renderInventory(inv) {
    $('#inventoryValue').innerHTML = `
      <div class="kv"><span>Unidades totales en almacén</span><span>${number(inv.units)}</span></div>
      <div class="kv"><span>Invertido (precio de compra)</span><span>${money(inv.cost_value)}</span></div>
      <div class="kv"><span>Valor de venta</span><span>${money(inv.retail_value)}</span></div>
      <div class="kv" style="font-size:.95rem">
        <span style="font-weight:600;color:var(--gris-texto)">Ganancia potencial</span>
        <span style="color:var(--exito);font-weight:800">${money(inv.potential_profit)}</span>
      </div>
      <div class="notice info" style="margin-top:14px">
        <span>💡</span>
        <div>Esta es la ganancia que obtendrías <b>si vendieras todo tu inventario al precio de venta</b>.</div>
      </div>`;
  }

  /* ------------------------------------------------------------- Carga */
  async function load() {
    try {
      const data = await get('/api/stats');
      renderSummary(data.summary);
      renderChart(data.series);
      renderDonut(data.by_category);
      renderTop(data.top_products);
      renderInventory(data.inventory);
      $('#noStats').style.display = data.has_data ? 'none' : 'flex';
    } catch (error) {
      Shevelle.toast(error.message, 'error', 'No se pudieron cargar las estadísticas');
    }
  }

  document.addEventListener('DOMContentLoaded', load);
})();
