/* ==========================================================================
   Modulo Productos - listado, busqueda, filtros y edicion
   ========================================================================== */

(() => {
  const { $, get, del, money, number, escapeHtml, categoryIcon, toast, confirmAction } = Shevelle;

  const grid = $('#productsGrid');
  if (!grid) return;

  let allProducts = [];

  /* ------------------------------------------------- Tarjeta de producto */
  function productCard(product) {
    const stockTag = product.stock <= 0
      ? '<span class="tag danger">🔴 Agotado</span>'
      : (product.low_stock
          ? '<span class="tag warn">⚠️ Inventario bajo</span>'
          : `<span class="tag ok">✓ ${number(product.stock)} disponibles</span>`);

    const image = product.image
      ? `<img src="${escapeHtml(product.image)}" alt="${escapeHtml(product.name)}"
               onerror="this.parentElement.textContent='${categoryIcon(product.category)}'">`
      : categoryIcon(product.category);

    return `
      <div class="product-card" data-id="${product.id}">
        <div class="product-img">
          ${image}
          ${stockTag}
        </div>
        <div class="product-body">
          <h3>${escapeHtml(product.name)}</h3>
          <div class="cat">${escapeHtml(product.category)}</div>
          <p class="desc">${escapeHtml(product.description || 'Sin descripción.')}</p>
          <div class="product-meta">
            <div>
              <div class="product-price">${money(product.sale_price)}</div>
              <div class="product-cost">Compra: ${money(product.purchase_price)} · +${money(product.profit_unit)}</div>
            </div>
            <div class="product-actions">
              <button class="btn btn-ghost btn-icon btn-sm" data-action="edit" title="Editar">✏️</button>
              <button class="btn btn-danger btn-icon btn-sm" data-action="delete" title="Eliminar">🗑️</button>
            </div>
          </div>
        </div>
      </div>`;
  }

  /* --------------------------------------------------------- Renderizado */
  function render() {
    if (!allProducts.length) {
      const hasFilters = ($('#searchInput')?.value || '') || ($('#categoryFilter')?.value !== 'Todas')
                     || ($('#stockFilter')?.value || '') || ($('#orderSelect')?.value !== 'recent');
      grid.innerHTML = `
        <div class="card" style="grid-column:1/-1">
          <div class="empty">
            <div class="big">${hasFilters ? '🔍' : '📦'}</div>
            <h3>${hasFilters ? 'No se encontraron productos' : 'Todavía no tienes productos'}</h3>
            <p>${hasFilters
                ? 'Prueba con otra palabra o quita los filtros de búsqueda.'
                : 'Agrega tu primer producto para empezar a vender y controlar tu inventario.'}</p>
            ${hasFilters
                ? '<button class="btn btn-ghost btn-sm" id="clearFilters">Quitar filtros</button>'
                : '<button class="btn btn-primary btn-sm" id="emptyNewBtn">➕ Agregar producto</button>'}
          </div>
        </div>`;
      $('#clearFilters')?.addEventListener('click', clearFilters);
      $('#emptyNewBtn')?.addEventListener('click', () => $('#newProductBtn').click());
      return;
    }

    grid.innerHTML = allProducts.map(productCard).join('');

    const totalStock = allProducts.reduce((sum, p) => sum + Number(p.stock || 0), 0);
    $('#resultCount').textContent = `${allProducts.length} producto(s)`;
    $('#totalStock').textContent  = `${number(totalStock)} unidades en total`;
  }

  /* --------------------------------------------------------- Carga datos */
  async function load() {
    const params = new URLSearchParams();
    const search   = $('#searchInput')?.value.trim();
    const category = $('#categoryFilter')?.value;
    const stock    = $('#stockFilter')?.value;
    const order    = $('#orderSelect')?.value;

    if (search)   params.set('search', search);
    if (category && category !== 'Todas') params.set('category', category);
    if (stock)    params.set('stock', stock);
    if (order)    params.set('order', order);

    try {
      const data = await get(`/api/products?${params.toString()}`);
      allProducts = data.products;
      render();
    } catch (error) {
      grid.innerHTML = `<div class="card" style="grid-column:1/-1">
        <div class="notice err"><span>❌</span><div>${escapeHtml(error.message)}</div></div></div>`;
      toast(error.message, 'error', 'Error al cargar productos');
    }
  }

  function clearFilters() {
    $('#searchInput').value = '';
    $('#categoryFilter').value = 'Todas';
    $('#stockFilter').value = '';
    $('#orderSelect').value = 'recent';
    load();
  }

  /* ------------------------------------------------------------ Acciones */
  grid.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-action]');
    if (!button) return;

    const card = button.closest('[data-id]');
    const product = allProducts.find((p) => String(p.id) === card.dataset.id);
    if (!product) return;

    if (button.dataset.action === 'edit') {
      window.editProduct(product);
      return;
    }

    if (button.dataset.action === 'delete') {
      const ok = await confirmAction(
        `¿Seguro que quieres eliminar "${product.name}"? Esta acción no se puede deshacer.`,
        'Eliminar producto'
      );
      if (!ok) return;

      try {
        const result = await del(`/api/products/${product.id}`);
        toast(result.message, 'ok');
        load();
        window.dispatchEvent(new CustomEvent('product:changed'));
      } catch (error) {
        toast(error.message, 'error', 'No se pudo eliminar');
      }
    }
  });

  /* ------------------------------------------------------ Filtros y busqueda */
  let searchTimer;
  $('#searchInput')?.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(load, 320);
  });
  $('#categoryFilter')?.addEventListener('change', load);
  $('#stockFilter')?.addEventListener('change', load);
  $('#orderSelect')?.addEventListener('change', load);

  /* --------- Si se llega con ?search= o ?stock= desde el Dashboard -------- */
  function applyUrlFilters() {
    const params = new URLSearchParams(window.location.search);
    const search = params.get('search');
    const stock  = params.get('stock');
    if (search) $('#searchInput').value = search;
    if (stock === 'low') $('#stockFilter').value = 'low';
  }

  document.addEventListener('DOMContentLoaded', () => {
    applyUrlFilters();
    load();
  });

  window.addEventListener('product:changed', load);
})();
