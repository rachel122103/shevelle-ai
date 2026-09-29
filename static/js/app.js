/* ==========================================================================
   Shevelle AI - JavaScript principal
   Funciones compartidas: API, notificaciones, modales, formato de dinero.
   ========================================================================== */

const Shevelle = (() => {

  /* ------------------------------------------------------- Moneda actual */
  let CURRENCY = (document.body.dataset.currency) || 'RD$';

  /* --------------------------------------------------------- Utilidades */
  const $  = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const escapeHtml = (value) => {
    const div = document.createElement('div');
    div.textContent = (value ?? '').toString();
    return div.innerHTML;
  };

  const money = (value) => {
    const number = Number(value || 0);
    return `${CURRENCY} ${number.toLocaleString('es-DO', {
      minimumFractionDigits: 2, maximumFractionDigits: 2
    })}`;
  };

  const number = (value) => Number(value || 0).toLocaleString('es-DO');

  /* Formato: "2026-09-29 15:04:00" -> "29/09/2026 3:04 p.m." */
  const formatDate = (value) => {
    if (!value) return '—';
    const date = new Date(String(value).replace(' ', 'T'));
    if (isNaN(date)) return value;
    return date.toLocaleDateString('es-DO', { day: '2-digit', month: '2-digit', year: 'numeric' })
         + ' ' + date.toLocaleTimeString('es-DO', { hour: 'numeric', minute: '2-digit' });
  };

  /* Formato relativo para el chat */
  const timeAgo = (value) => {
    const date = new Date(String(value).replace(' ', 'T'));
    if (isNaN(date)) return '';
    const minutes = Math.floor((Date.now() - date) / 60000);
    if (minutes < 1) return 'ahora';
    if (minutes < 60) return `hace ${minutes} min`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `hace ${hours} h`;
    return `hace ${Math.floor(hours / 24)} d`;
  };

  /* Emoji de la categoría para las tarjetas de producto */
  const CATEGORY_ICONS = {
    'Accesorios': '💎', 'Aretes': '🦋', 'Collares': '📿', 'Pulseras': '⭕',
    'Pinzas': '💇', 'Maquillaje': '💄', 'Skincare': '🧴', 'Otros': '🎀'
  };
  const categoryIcon = (category) => CATEGORY_ICONS[category] || '🎀';

  /* ------------------------------------------------------- Peticiones API */
  async function api(path, options = {}) {
    const config = { headers: {}, ...options };
    if (config.body && !(config.body instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
      config.body = JSON.stringify(config.body);
    }

    let response;
    try {
      response = await fetch(path, config);
    } catch (error) {
      throw new Error('No se pudo conectar con el servidor. ¿Está corriendo la aplicación?');
    }

    let data = null;
    try { data = await response.json(); } catch (error) { data = null; }

    if (!response.ok) {
      const message = (data && data.message) || `Error ${response.status}`;
      const error = new Error(message);
      error.status = response.status;
      error.data = data;
      throw error;
    }
    return data;
  }

  const get  = (path)    => api(path);
  const post = (path, body) => api(path, { method: 'POST', body: body || {} });
  const put  = (path, body) => api(path, { method: 'PUT',  body: body || {} });
  const del  = (path)    => api(path, { method: 'DELETE' });

  /* -------------------------------------------------------- Notificaciones */
  const TOAST_ICONS = { ok: '✅', error: '❌', warn: '⚠️', info: '💡' };

  function toast(message, type = 'ok', title = '') {
    const box = $('#toasts');
    if (!box) return;

    const element = document.createElement('div');
    element.className = `toast ${type}`;
    element.innerHTML = `
      <span class="t-ico">${TOAST_ICONS[type] || '💡'}</span>
      <div>
        ${title ? `<strong>${escapeHtml(title)}</strong>` : ''}
        <p>${escapeHtml(message)}</p>
      </div>`;
    box.appendChild(element);

    setTimeout(() => {
      element.classList.add('hide');
      setTimeout(() => element.remove(), 320);
    }, type === 'error' ? 6000 : 3800);
  }

  /* ------------------------------------------------------------- Modales */
  function openModal(id)  { const m = document.getElementById(id); if (m) m.classList.add('open'); }
  function closeModal(id) { const m = document.getElementById(id); if (m) m.classList.remove('open'); }

  /* Confirmación reutilizable: devuelve una promesa true/false */
  function confirmAction(text, title = '¿Estás segura?') {
    return new Promise((resolve) => {
      const modal = $('#confirmModal');
      if (!modal) return resolve(window.confirm(text));

      $('#confirmTitle').textContent = title;
      $('#confirmText').textContent = text;
      openModal('confirmModal');

      const accept = $('#confirmAccept');
      const clean = () => {
        accept.removeEventListener('click', onYes);
        modal.removeEventListener('click', onNo);
        document.removeEventListener('keydown', onKey);
      };
      const onYes = () => { clean(); closeModal('confirmModal'); resolve(true); };
      const onNo  = () => { clean(); closeModal('confirmModal'); resolve(false); };
      const onKey = (event) => { if (event.key === 'Escape') onNo(); };

      accept.addEventListener('click', onYes);
      modal.addEventListener('click', (event) => { if (event.target === modal) onNo(); });
      document.addEventListener('keydown', onKey);
    });
  }

  /* ------------------------------------------------------ Menú adaptable */
  function initMenu() {
    const sidebar = $('#sidebar');
    const overlay = $('#overlay');
    const burger  = $('#burger');

    const close = () => { sidebar?.classList.remove('open'); overlay?.classList.remove('show'); };
    const toggle = () => {
      sidebar?.classList.toggle('open');
      overlay?.classList.toggle('show');
    };

    burger?.addEventListener('click', toggle);
    overlay?.addEventListener('click', close);
    $$('.nav-item').forEach((item) => item.addEventListener('click', close));
    document.addEventListener('keydown', (event) => { if (event.key === 'Escape') close(); });
  }

  /* --------------------------------------------- Cierre de modales (X) */
  function initModals() {
    $$('[data-close-modal]').forEach((button) => {
      button.addEventListener('click', () => closeModal(button.dataset.closeModal));
    });
    $$('.modal').forEach((modal) => {
      modal.addEventListener('click', (event) => { if (event.target === modal) closeModal(modal.id); });
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') $$('.modal.open').forEach((m) => m.classList.remove('open'));
    });
  }

  /* --------------------------------------------- Formulario de producto */
  function initProductModal() {
    const modal  = $('#productModal');
    const form   = $('#productForm');
    if (!modal || !form) return;

    // Abrir en modo "crear"
    $('#newProductBtn')?.addEventListener('click', () => {
      form.reset();
      $('#productId').value = '';
      $('#productModalTitle').textContent = '➕ Agregar producto';
      $('#productSubmit').textContent = '💾 Guardar producto';
      $('#productMarginBox').style.display = 'none';
      openModal('productModal');
      setTimeout(() => $('#productName')?.focus(), 120);
    });

    // Abrir en modo "editar" (lo llama el módulo de productos)
    window.editProduct = (product) => {
      form.reset();
      $('#productId').value          = product.id;
      $('#productName').value        = product.name;
      $('#productCategory').value    = product.category;
      $('#productStock').value       = product.stock;
      $('#productPurchase').value    = product.purchase_price;
      $('#productSale').value        = product.sale_price;
      $('#productDescription').value = product.description || '';
      $('#productModalTitle').textContent = `✏️ Editar: ${product.name}`;
      $('#productSubmit').textContent = '💾 Guardar cambios';
      updateMargin();
      openModal('productModal');
    };

    // Margen en vivo
    const updateMargin = () => {
      const purchase = Number($('#productPurchase')?.value || 0);
      const sale     = Number($('#productSale')?.value || 0);
      const box      = $('#productMarginBox');
      if (!box) return;
      if (!purchase && !sale) { box.style.display = 'none'; return; }
      box.style.display = 'block';
      $('#marginFormula').textContent = `${sale.toFixed(2)} - ${purchase.toFixed(2)}`;
      const profit = sale - purchase;
      $('#marginValue').textContent = money(profit);
      $('#marginValue').style.color = profit >= 0 ? 'var(--exito)' : 'var(--peligro)';
    };
    $('#productPurchase')?.addEventListener('input', updateMargin);
    $('#productSale')?.addEventListener('input', updateMargin);

    // Guardar
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = $('#productSubmit');
      const id     = $('#productId').value;
      const payload = {
        name:        $('#productName').value.trim(),
        category:    $('#productCategory').value,
        description: $('#productDescription').value.trim(),
        purchase_price: $('#productPurchase').value,
        sale_price:     $('#productSale').value,
        stock:       $('#productStock').value
      };

      if (!payload.name) return toast('El nombre del producto es obligatorio.', 'error');

      const fileInput = $('#productImage');
      const hasImage   = fileInput && fileInput.files.length > 0;
      const formData   = new FormData();
      Object.entries(payload).forEach(([key, value]) => formData.append(key, value));
      if (hasImage) formData.append('image', fileInput.files[0]);

      button.disabled = true;
      button.textContent = '⏳ Guardando...';
      try {
        const result = id
          ? await api(`/api/products/${id}`, { method: 'PUT', body: formData })
          : await api('/api/products', { method: 'POST', body: formData });
        closeModal('productModal');
        toast(result.message, 'ok');
        window.dispatchEvent(new CustomEvent('product:changed'));
      } catch (error) {
        toast(error.message, 'error', 'No se pudo guardar');
      } finally {
        button.disabled = false;
        button.textContent = id ? '💾 Guardar cambios' : '💾 Guardar producto';
      }
    });
  }

  /* ------------------------------------------------------------- Arranque */
  function init() {
    initMenu();
    initModals();
    initProductModal();

    // Cierra el menu si se hace clic fuera (movil)
    document.addEventListener('click', (event) => {
      const sidebar = $('#sidebar');
      if (window.innerWidth <= 992 && sidebar?.classList.contains('open')
          && !sidebar.contains(event.target) && event.target !== $('#burger')) {
        sidebar.classList.remove('open');
        $('#overlay')?.classList.remove('show');
      }
    });
  }

  document.addEventListener('DOMContentLoaded', init);

  /* ------------------------------------------------- API publica (modulos) */
  return { $, $$, api, get, post, put, del, toast, openModal, closeModal, confirmAction,
           money, number, formatDate, timeAgo, escapeHtml, categoryIcon,
           get currency() { return CURRENCY; },
           set currency(value) { CURRENCY = value; } };
})();
