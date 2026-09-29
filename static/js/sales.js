/* ==========================================================================
   Modulo Ventas - registrar ventas y ver el historial
   ========================================================================== */

(() => {
  const form = $('#saleForm');
  if (!form) return;

  const { $, get, post, del, money, number, formatDate, escapeHtml, categoryIcon, toast, confirmAction } = Shevelle;

  let catalog = [];
  let selected = null;

  /* ------------------------------------------------- Selector de producto */
  function renderPickerList(filter = '') {
    const list = $('#productList');
    const term  = filter.toLowerCase();

    const matches = catalog.filter((p) =>
      !term || p.name.toLowerCase().includes(term) || p.category.toLowerCase().includes(term)
    );

    if (!matches.length) {
      list.innerHTML = '<div class="picker-item"><small>Ningún producto coincide con tu búsqueda.</small></div>';
      return;
    }

    list.innerHTML = matches.map((p) => `
      <div class="picker-item ${p.stock <= 0 ? 'out' : ''}" data-id="${p.id}">
        <div>
          <strong>${categoryIcon(p.category)} ${escapeHtml(p.name)}</strong><br>
          <small>${escapeHtml(p.category)} · ${p.stock <= 0 ? 'agotado' : `${p.stock} disponibles`}</small>
        </div>
        <strong>${money(p.sale_price)}</strong>
      </div>`).join('');
  }

  function selectProduct(product) {
    selected = product;
    $('#saleProductId').value = product.id;
    $('#productSearch').value = product.name;
    $('#productList').classList.remove('open');

    $('#salePrice').value = product.sale_price;
    $('#selectedProductHint').innerHTML =
      `Seleccionado: <b>${escapeHtml(product.name)}</b> · precio ${money(product.sale_price)} · ` +
      `compra ${money(product.purchase_price)} · <b>${product.stock}</b> disponibles`;

    $('#saleSubmit').disabled = false;
    calculate();
  }

  /* ----------------------------------------------------- Calculo en vivo */
  function calculate() {
    const quantity = Math.max(1, Number($('#saleQuantity').value || 1));
    const priceRaw = $('#salePrice').value;

    if (!selected) {
      $('#calcTotal').textContent  = `${Shevelle.currency} 0.00`;
      $('#calcProfit').textContent = `${Shevelle.currency} 0.00`;
      $('#calcStock').textContent  = '—';
      return;
    }

    const price = priceRaw === '' ? Number(selected.sale_price) : Number(priceRaw);
    const total  = price * quantity;
    const profit = (price - Number(selected.purchase_price)) * quantity;

    $('#calcTotal').textContent  = money(total);
    $('#calcProfit').textContent = money(profit);
    $('#formulaTotal').textContent  = `${price.toFixed(2)} x ${quantity} = ${total.toFixed(2)}`;
    $('#formulaProfit').textContent = `(${price.toFixed(2)} - ${Number(selected.purchase_price).toFixed(2)}) x ${quantity} = ${profit.toFixed(2)}`;

    const stockCell = $('#calcStock');
    const enough = selected.stock >= quantity;
    stockCell.innerHTML = enough
      ? `<span style="color:var(--exito);font-weight:700">${selected.stock} unidades</span>`
      : `<span style="color:var(--peligro);font-weight:700">⚠️ Solo hay ${selected.stock} unidades</span>`;

    $('#saleSubmit').disabled = !enough;
  }

  /* ------------------------------------------------------- Registrar venta */
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!selected) return toast('Selecciona un producto primero.', 'error');

    const quantity = Math.max(1, Number($('#saleQuantity').value || 1));
    const priceRaw = $('#salePrice').value;

    if (quantity > selected.stock) {
      return toast(`No hay suficiente inventario. Solo quedan ${selected.stock} unidades.`, 'error');
    }

    const payload = {
      product_id: selected.id,
      quantity,
      customer: $('#saleCustomer').value.trim(),
      payment_method: $('#salePayment').value
    };
    if (priceRaw !== '') payload.sale_price = priceRaw;

    const button = $('#saleSubmit');
    button.disabled = true;
    button.textContent = '⏳ Registrando...';

    try {
      const result = await post('/api/sales', payload);
      toast(result.message, 'ok');
      if (result.low_stock_warning) toast(result.low_stock_warning, 'warn', 'Inventario bajo');

      // Refresca el producto seleccionado con el stock nuevo
      const updated = catalog.find((p) => p.id === selected.id);
      if (updated) { updated.stock = result.product.stock; }
      selectProduct(selected);

      form.reset();
      selected = null;
      $('#saleProductId').value = '';
      $('#selectedProductHint').textContent = 'Ningún producto seleccionado todavía.';
      $('#saleSubmit').disabled = true;
      $('#calcTotal').textContent = `${Shevelle.currency} 0.00`;
      $('#calcProfit').textContent = `${Shevelle.currency} 0.00`;
      $('#calcStock').textContent = '—';

      await Promise.all([loadCatalog(), loadSales()]);
    } catch (error) {
      toast(error.message, 'error', 'No se pudo registrar la venta');
    } finally {
      button.textContent = '✅ Registrar venta';
      calculate();
    }
  });

  /* --------------------------------------------------------- Historial */
  async function loadSales() {
    const body = $('#salesTable');
    try {
      const data = await get('/api/sales?limit=60');

      $('#salesCount').textContent = `${data.count} venta(s) mostradas`;
      $('#todaySales').textContent  = number(data.summary.day.sales);
      $('#todayProfit').textContent = money(data.summary.day.profit);

      if (!data.sales.length) {
        body.innerHTML = `<tr><td colspan="7">
          <div class="empty">
            <div class="big">🛒</div>
            <h3>Aún no hay ventas</h3>
            <p>Usa el formulario para registrar tu primera venta.</p>
          </div></td></tr>`;
        return;
      }

      body.innerHTML = data.sales.map((sale) => `
        <tr>
          <td>
            <div style="display:flex;align-items:center;gap:9px">
              <span style="font-size:1.1rem">${categoryIcon(sale.category)}</span>
              <div>
                <strong>${escapeHtml(sale.product_name)}</strong><br>
                <small style="color:var(--gris-tenue)">${escapeHtml(sale.payment_method)}${sale.customer ? ' · ' + escapeHtml(sale.customer) : ''}</small>
              </div>
            </div>
          </td>
          <td class="num">${number(sale.quantity)}</td>
          <td class="num">${money(sale.sale_price)}</td>
          <td class="num"><strong>${money(sale.total)}</strong></td>
          <td class="num" style="color:var(--exito);font-weight:600">+${money(sale.profit)}</td>
          <td><small style="color:var(--gris-tenue)">${escapeHtml(formatDate(sale.created_at))}</small></td>
          <td class="num">
            <button class="btn btn-danger btn-icon btn-sm" data-sale="${sale.id}" title="Anular venta">🗑️</button>
          </td>
        </tr>`).join('');
    } catch (error) {
      body.innerHTML = `<tr><td colspan="7">
        <div class="notice err"><span>❌</span><div>${escapeHtml(error.message)}</div></div></td></tr>`;
    }
  }

  $('#salesTable')?.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-sale]');
    if (!button) return;

    const ok = await confirmAction(
      'Al anular esta venta se devolverán las unidades al inventario. ¿Continuar?',
      'Anular venta'
    );
    if (!ok) return;

    try {
      const result = await del(`/api/sales/${button.dataset.sale}`);
      toast(result.message, 'ok');
      await Promise.all([loadCatalog(), loadSales()]);
    } catch (error) {
      toast(error.message, 'error', 'No se pudo anular la venta');
    }
  });

  $('#refreshSales')?.addEventListener('click', () => {
    loadSales();
    toast('Historial actualizado.', 'info');
  });

  /* ------------------------------------------------------ Cargar catálogo */
  async function loadCatalog() {
    try {
      const data = await get('/api/products?stock=available');
      catalog = data.products;
    } catch (error) {
      toast(error.message, 'error', 'No se pudieron cargar los productos');
    }
  }

  /* --------------------------------------------------------- Eventos */
  $('#productSearch')?.addEventListener('focus', () => {
    renderPickerList($('#productSearch').value);
    $('#productList').classList.add('open');
  });

  $('#productSearch')?.addEventListener('input', () => {
    renderPickerList($('#productSearch').value);
    $('#productList').classList.add('open');
  });

  $('#productList')?.addEventListener('click', (event) => {
    const item = event.target.closest('.picker-item[data-id]');
    if (!item) return;
    const product = catalog.find((p) => String(p.id) === item.dataset.id);
    if (!product) return;
    if (product.stock <= 0) return toast('Ese producto está agotado.', 'warn');
    selectProduct(product);
  });

  document.addEventListener('click', (event) => {
    if (!event.target.closest('.product-picker')) $('#productList')?.classList.remove('open');
  });

  $('#saleQuantity')?.addEventListener('input', calculate);
  $('#salePrice')?.addEventListener('input', calculate);

  /* ------------------------------------------------------------- Arranque */
  document.addEventListener('DOMContentLoaded', async () => {
    await loadCatalog();
    renderPickerList('');
    await loadSales();
  });
})();
