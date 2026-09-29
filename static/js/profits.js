/* ==========================================================================
   Modulo Ganancias - tarjetas de periodos y grafico de barras
   ========================================================================== */

(() => {
  const { $, get, money, number, escapeHtml } = Shevelle;
  if (!$('#profitDay')) return;

  /* --------------------------------------------------------- Tarjetas */
  function renderCards(summary) {
    const set = (id, footId, data, extra) => {
      $(id).textContent = money(data.profit);
      $(footId).textContent = `${number(data.sales)} venta(s) · ${money(data.revenue)} en ingresos`;
    };

    set('#profitDay', '#profitDayFoot', summary.day);
    set('#profitWeek', '#profitWeekFoot', summary.week);
    set('#profitMonth', '#profitMonthFoot', summary.month);
    set('#profitAll', '#profitAllFoot', summary.all);

    if (summary.all.sales > 0) {
      $('#profitAllFoot').textContent =
        `${number(summary.all.sales)} venta(s) · ${number(summary.all.units)} unidades vendidas`;
    }
  }

  /* ------------------------------------------------- Tabla por periodo */
  function renderTable(summary) {
    const rows = [
      ['Hoy', summary.day],
      ['Esta semana', summary.week],
      ['Este mes', summary.month],
      ['Todo el tiempo', summary.all]
    ];

    $('#profitTable').innerHTML = rows.map(([label, data]) => `
      <tr>
        <td><strong>${label}</strong></td>
        <td class="num">${number(data.sales)}</td>
        <td class="num">${number(data.units)}</td>
        <td class="num">${money(data.revenue)}</td>
        <td class="num" style="color:var(--exito);font-weight:600">${money(data.profit)}</td>
      </tr>`).join('');
  }

  /* ---------------------------------------------- Grafico de barras */
  function renderChart(series) {
    const box = $('#weeklyChart');
    const max = Math.max(...series.map((d) => d.revenue), 1);

    box.innerHTML = `
      <div class="bars">
        ${series.map((day) => {
          const revenueHeight = Math.max(2, (day.revenue / max) * 100);
          const profitHeight  = day.revenue > 0
            ? Math.max(2, Math.min(revenueHeight, (day.profit / day.revenue) * revenueHeight))
            : 0;
          return `
            <div class="bar-col">
              <span class="bar-value">${day.revenue > 0 ? money(day.revenue).replace(/\.00$/, '') : ''}</span>
              <div class="bar-track" title="${escapeHtml(day.date)}: ${money(day.revenue)} ingresos, ${money(day.profit)} ganancia">
                <div class="bar-fill" style="height:${revenueHeight}%"></div>
                ${profitHeight > 0 ? `<div class="bar-fill gold" style="position:absolute;bottom:0;width:100%;height:${profitHeight}%"></div>` : ''}
              </div>
              <span class="bar-label">${escapeHtml(day.label)}</span>
            </div>`;
        }).join('')}
      </div>
      <p style="text-align:center;font-size:.75rem;color:var(--gris-tenue);margin-top:12px">
        💜 Barra lila = ingresos &nbsp;·&nbsp; 💛 Barra dorada = ganancia
      </p>`;
  }

  /* ------------------------------------------ Top productos por ganancia */
  function renderTop(list) {
    const box = $('#profitTopProducts');
    if (!list.length) {
      box.innerHTML = `
        <div class="empty">
          <div class="big">🏆</div>
          <h3>Todavía no hay suficientes datos para mostrar estadísticas.</h3>
          <p>Registra ventas y aquí verás qué productos te dejan más ganancia.</p>
        </div>`;
      return;
    }

    const max = Math.max(...list.map((item) => item.profit)) || 1;
    box.innerHTML = list.map((item) => `
      <div class="hbar">
        <div class="hbar-top">
          <strong>${escapeHtml(item.name)}</strong>
          <span class="num">${money(item.profit)}</span>
        </div>
        <div class="hbar-track">
          <div class="hbar-fill gold" style="width:${(item.profit / max) * 100}%"></div>
        </div>
        <small style="color:var(--gris-tenue)">${number(item.units)} unidad(es) vendidas · ${money(item.revenue)} en ingresos</small>
      </div>`).join('');
  }

  /* ------------------------------------------------------------- Carga */
  async function load() {
    try {
      const data = await get('/api/profits?period=day');
      const hasData = data.summary.all.sales > 0;

      renderCards(data.summary);
      renderTable(data.summary);
      renderChart(data.series);
      renderTop(data.top_products);

      $('#noDataNotice').style.display = hasData ? 'none' : 'flex';
    } catch (error) {
      Shevelle.toast(error.message, 'error', 'No se pudieron cargar las ganancias');
    }
  }

  document.addEventListener('DOMContentLoaded', load);
})();
