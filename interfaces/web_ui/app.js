// Estado global de la aplicación web
const state = {
  token: localStorage.getItem('token') || '',
  currentUser: JSON.parse(localStorage.getItem('currentUser') || 'null') || {
    username: 'admin',
    role: 'ADMIN',
    full_name: 'Administrador Tienda'
  },
  products: [],
  cart: [],
  festivities: [],
  alerts: []
};

// Utilidad para llamadas API con token
async function apiCall(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }

  const response = await fetch(`/api${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    console.warn("Sesión expirada o no autenticado. Reautenticando como admin por defecto...");
    await loginAs('admin', 'admin123');
    return apiCall(endpoint, options);
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Error en la petición' }));
    throw new Error(errorData.detail || 'Ocurrió un error');
  }

  return response.json();
}

// Inicialización
document.addEventListener('DOMContentLoaded', async () => {
  if (!state.token) {
    await loginAs('admin', 'admin123');
  } else {
    updateUserUI();
    loadDashboard();
    loadProducts();
  }
});

// Manejo de roles y autenticación (RF01, RF02, RNF04)
async function loginAs(username, password) {
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
      alert("Error al iniciar sesión.");
      return;
    }

    const data = await res.json();
    state.token = data.access_token;
    state.currentUser = {
      username: data.username,
      role: data.role,
      full_name: data.full_name
    };

    localStorage.setItem('token', state.token);
    localStorage.setItem('currentUser', JSON.stringify(state.currentUser));

    updateUserUI();
    toggleRoleSwitchModal(false);
    loadDashboard();
    loadProducts();
    if (state.currentUser.role === 'ADMIN') {
      loadFestivities();
      loadRecommendations();
    }
  } catch (err) {
    console.error("Login error:", err);
  }
}

function updateUserUI() {
  const roleTag = document.getElementById('userRoleTag');
  const userName = document.getElementById('userName');
  
  if (roleTag) {
    roleTag.textContent = state.currentUser.role;
    roleTag.className = `user-role-tag ${state.currentUser.role.toLowerCase()}`;
  }
  if (userName) {
    userName.textContent = state.currentUser.full_name;
  }

  // Ocultar o mostrar elementos exclusivos de administrador (RF02, RNF04)
  const isAdmin = state.currentUser.role === 'ADMIN';
  document.querySelectorAll('.admin-only').forEach(el => {
    el.style.display = isAdmin ? '' : 'none';
  });
}

function toggleRoleSwitchModal(show) {
  const modal = document.getElementById('roleModal');
  if (show === undefined) {
    modal.classList.toggle('open');
  } else {
    modal.classList.toggle('open', show);
  }
}

// Navegación entre pestañas
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-view').forEach(view => view.classList.remove('active'));

  const targetView = document.getElementById(`tab-${tabId}`);
  if (targetView) targetView.classList.add('active');

  const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick')?.includes(`'${tabId}'`));
  if (activeBtn) activeBtn.classList.add('active');

  if (tabId === 'dashboard') loadDashboard();
  if (tabId === 'sales') loadSalesCatalog();
  if (tabId === 'inventory') loadProducts();
  if (tabId === 'festivities' && state.currentUser.role === 'ADMIN') loadFestivities();
  if (tabId === 'recommendations' && state.currentUser.role === 'ADMIN') loadRecommendations();
}

// ================= DASHBOARD (RF15) =================
async function loadDashboard() {
  try {
    const data = await apiCall('/dashboard');
    
    // Métricas
    const sales = data.sales_today || {};
    document.getElementById('dashTodaySales').textContent = formatCurrency(sales.total_sales_amount || 0);
    document.getElementById('dashTxCount').textContent = `${sales.transaction_count || 0} transacciones registradas hoy`;

    const inv = data.inventory_overview || {};
    document.getElementById('dashLowStockCount').textContent = inv.low_stock || 0;
    document.getElementById('dashOutOfStockCount').textContent = inv.out_of_stock || 0;

    const recs = data.recommendations || [];
    const aiRecEl = document.getElementById('dashAiRecCount');
    if (aiRecEl) aiRecEl.textContent = recs.length;

    // Lista de Alertas
    const alertsList = document.getElementById('dashAlertsList');
    if (alertsList) {
      const alerts = data.alerts || [];
      if (alerts.length === 0) {
        alertsList.innerHTML = '<p class="empty-state">No hay alertas de inventario críticas. Todo en orden.</p>';
      } else {
        alertsList.innerHTML = alerts.map(a => `
          <div style="padding: 10px 0; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center;">
            <div>
              <strong>${a.product_name}</strong>
              <div style="font-size: 0.8rem; color: #64748b;">${a.message}</div>
            </div>
            <span class="badge ${a.alert_type === 'AGOTADO' ? 'badge-danger' : 'badge-warning'}">
              ${a.alert_type} (${a.stock_actual} disp.)
            </span>
          </div>
        `).join('');
      }
    }

    // Top productos vendidos hoy
    const topList = document.getElementById('dashTopProductsList');
    if (topList) {
      const top = data.top_moving_products || [];
      if (top.length === 0) {
        topList.innerHTML = '<p class="empty-state">No hay ventas registradas el día de hoy todavía.</p>';
      } else {
        topList.innerHTML = top.map((p, idx) => `
          <div style="padding: 10px 0; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center;">
            <div>
              <span style="font-weight: 700; color: #1e3a8a; margin-right: 8px;">#${idx + 1}</span>
              <strong>${p.name}</strong>
            </div>
            <div style="text-align: right;">
              <span class="badge badge-success">${p.units_sold} unidades</span>
              <div style="font-size: 0.78rem; color: #64748b;">${formatCurrency(p.revenue)}</div>
            </div>
          </div>
        `).join('');
      }
    }

  } catch (err) {
    console.error("Error loading dashboard:", err);
  }
}

// ================= VENTAS Y CARRITO (RF06, RF07, HU03) =================
async function loadSalesCatalog() {
  await loadProducts();
  filterSalesCatalog();
}

function filterSalesCatalog() {
  const query = (document.getElementById('salesSearchInput')?.value || '').toLowerCase();
  const grid = document.getElementById('salesProductGrid');
  if (!grid) return;

  const filtered = state.products.filter(p => 
    p.name.toLowerCase().includes(query) || 
    p.category.toLowerCase().includes(query) ||
    p.code.toLowerCase().includes(query)
  );

  grid.innerHTML = filtered.map(p => `
    <div class="product-card" onclick="addToCart(${p.id})">
      <div>
        <div class="product-card-title">${p.name}</div>
        <div class="product-card-cat">${p.category} · Código: ${p.code}</div>
      </div>
      <div class="product-card-footer">
        <span class="product-card-price">${formatCurrency(p.price)}</span>
        <span class="product-card-stock ${p.stock_actual === 0 ? 'badge-danger' : (p.stock_actual <= p.stock_minimo ? 'badge-warning' : '')}">
          Stock: ${p.stock_actual}
        </span>
      </div>
    </div>
  `).join('');
}

function addToCart(productId) {
  const prod = state.products.find(p => p.id === productId);
  if (!prod) return;

  if (prod.stock_actual <= 0) {
    alert(`El producto "${prod.name}" está agotado en bodega.`);
    return;
  }

  const existing = state.cart.find(it => it.product.id === productId);
  if (existing) {
    if (existing.quantity + 1 > prod.stock_actual) {
      alert(`No puede agregar más de ${prod.stock_actual} unidades (stock máximo disponible).`);
      return;
    }
    existing.quantity += 1;
  } else {
    state.cart.push({ product: prod, quantity: 1 });
  }

  renderCart();
}

function updateCartQuantity(productId, delta) {
  const item = state.cart.find(it => it.product.id === productId);
  if (!item) return;

  item.quantity += delta;
  if (item.quantity <= 0) {
    state.cart = state.cart.filter(it => it.product.id !== productId);
  } else if (item.quantity > item.product.stock_actual) {
    alert(`Solo hay ${item.product.stock_actual} unidades disponibles.`);
    item.quantity = item.product.stock_actual;
  }

  renderCart();
}

function clearCart() {
  state.cart = [];
  renderCart();
}

function renderCart() {
  const container = document.getElementById('cartItemsList');
  const totalPriceEl = document.getElementById('cartTotalPrice');
  if (!container || !totalPriceEl) return;

  if (state.cart.length === 0) {
    container.innerHTML = '<p class="empty-state">Haga clic en un artículo del catálogo para agregarlo a la venta.</p>';
    totalPriceEl.textContent = '$0';
    return;
  }

  let total = 0;
  container.innerHTML = state.cart.map(it => {
    const subtotal = it.product.price * it.quantity;
    total += subtotal;
    return `
      <div class="cart-item">
        <div>
          <div style="font-weight: 600; font-size: 0.88rem;">${it.product.name}</div>
          <div style="font-size: 0.78rem; color: #64748b;">${formatCurrency(it.product.price)} c/u</div>
        </div>
        <div class="cart-item-qty">
          <button class="cart-qty-btn" onclick="updateCartQuantity(${it.product.id}, -1)">-</button>
          <span style="font-weight: 600; min-width: 20px; text-align: center;">${it.quantity}</span>
          <button class="cart-qty-btn" onclick="updateCartQuantity(${it.product.id}, 1)">+</button>
          <span style="font-weight: 700; margin-left: 10px; color: #1e3a8a;">${formatCurrency(subtotal)}</span>
        </div>
      </div>
    `;
  }).join('');

  totalPriceEl.textContent = formatCurrency(total);
}

async function processSale() {
  if (state.cart.length === 0) {
    alert("El carrito está vacío. Agregue productos antes de registrar la venta.");
    return;
  }

  const paymentMethod = document.getElementById('paymentMethodSelect')?.value || 'EFECTIVO';
  const payload = {
    payment_method: paymentMethod,
    items: state.cart.map(it => ({
      product_id: it.product.id,
      quantity: it.quantity
    }))
  };

  try {
    const res = await apiCall('/sales', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    alert(`¡Venta registrada con éxito!\nNúmero: ${res.sale_number}\nTotal cobrado: ${formatCurrency(res.total_amount)}\nEl inventario ha sido descontado automáticamente.`);
    clearCart();
    await loadProducts();
    await loadDashboard();
    switchTab('dashboard');
  } catch (err) {
    alert(`No se pudo registrar la venta: ${err.message}`);
  }
}

// ================= INVENTARIO (RF03, RF04, RF05, RF09) =================
async function loadProducts() {
  try {
    const products = await apiCall('/products');
    state.products = products;
    renderInventoryTable();
    filterSalesCatalog();
  } catch (err) {
    console.error("Error loading products:", err);
  }
}

function filterInventoryTable() {
  renderInventoryTable();
}

function renderInventoryTable() {
  const tbody = document.getElementById('inventoryTableBody');
  const query = (document.getElementById('inventorySearchInput')?.value || '').toLowerCase();
  if (!tbody) return;

  const filtered = state.products.filter(p => 
    p.name.toLowerCase().includes(query) || 
    p.code.toLowerCase().includes(query) || 
    p.category.toLowerCase().includes(query)
  );

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No se encontraron artículos con el criterio de búsqueda.</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(p => {
    let badgeClass = 'badge-success';
    let statusText = 'Normal';
    if (p.stock_actual === 0) {
      badgeClass = 'badge-danger';
      statusText = 'Agotado';
    } else if (p.stock_actual <= p.stock_minimo) {
      badgeClass = 'badge-warning';
      statusText = 'Stock Bajo';
    }

    return `
      <tr>
        <td><code>${p.code}</code></td>
        <td style="font-weight: 600;">${p.name}</td>
        <td><span class="badge badge-info">${p.category}</span></td>
        <td style="font-weight: 600;">${formatCurrency(p.price)}</td>
        <td style="font-weight: 700; color: ${p.stock_actual === 0 ? '#dc2626' : (p.stock_actual <= p.stock_minimo ? '#d97706' : '#15803d')};">
          ${p.stock_actual}
        </td>
        <td style="color: #64748b;">${p.stock_minimo}</td>
        <td><span class="badge ${badgeClass}">${statusText}</span></td>
      </tr>
    `;
  }).join('');
}

// Modales de Nuevo Producto
function openNewProductModal() {
  document.getElementById('newProductModal')?.classList.add('open');
}
function closeNewProductModal() {
  document.getElementById('newProductModal')?.classList.remove('open');
}
async function handleCreateProduct(e) {
  e.preventDefault();
  const payload = {
    code: document.getElementById('prodCode').value.trim() || undefined,
    category: document.getElementById('prodCategory').value,
    name: document.getElementById('prodName').value.trim(),
    price: parseFloat(document.getElementById('prodPrice').value),
    stock_actual: parseInt(document.getElementById('prodStock').value),
    stock_minimo: parseInt(document.getElementById('prodStockMin').value),
    description: document.getElementById('prodDesc').value.trim()
  };

  try {
    await apiCall('/products', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    alert("¡Producto registrado exitosamente!");
    closeNewProductModal();
    document.getElementById('newProductForm').reset();
    await loadProducts();
    await loadDashboard();
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

// ================= FESTIVIDADES (RF10, HU06) =================
async function loadFestivities() {
  try {
    const list = await apiCall('/festivities');
    state.festivities = list;
    const container = document.getElementById('festivitiesList');
    if (!container) return;

    if (list.length === 0) {
      container.innerHTML = '<p class="empty-state">No hay festividades registradas aún.</p>';
      return;
    }

    container.innerHTML = list.map(f => `
      <div class="festivity-card">
        <div class="festivity-title">${f.name}</div>
        <div class="festivity-dates">📅 Del ${f.start_date} al ${f.end_date}</div>
        <div class="festivity-factor">Factor Demanda: ${f.demand_factor}x</div>
        <p style="font-size: 0.84rem; color: #475569; margin: 6px 0;">${f.description || 'Sin descripción'}</p>
        <div style="font-size: 0.75rem; color: #64748b;">
          <strong>Afecta:</strong> ${f.affected_categories?.join(', ') || 'General'}
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error("Error loading festivities:", err);
  }
}

function openNewFestivityModal() {
  document.getElementById('newFestivityModal')?.classList.add('open');
}
function closeNewFestivityModal() {
  document.getElementById('newFestivityModal')?.classList.remove('open');
}
async function handleCreateFestivity(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById('festName').value.trim(),
    start_date: document.getElementById('festStart').value,
    end_date: document.getElementById('festEnd').value,
    demand_factor: parseFloat(document.getElementById('festFactor').value),
    affected_categories: document.getElementById('festCategories').value.split(',').map(s => s.trim()).filter(Boolean),
    description: document.getElementById('festDesc').value.trim()
  };

  try {
    await apiCall('/festivities', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    alert("Festividad religiosa registrada correctamente.");
    closeNewFestivityModal();
    document.getElementById('newFestivityForm').reset();
    await loadFestivities();
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

// ================= RECOMENDACIONES DE COMPRA IA (RF11, RF12, RF13, RF14, HU07) =================
async function loadRecommendations() {
  const container = document.getElementById('recommendationsContainer');
  if (!container) return;

  container.innerHTML = '<div class="loading-state">Analizando inventario, histórico de ventas y festividades con Inteligencia Artificial...</div>';

  try {
    const res = await apiCall('/recommendations?horizon_days=15&window_days=30');
    const data = res.result || {};
    const recs = data.recommendations || [];

    if (recs.length === 0) {
      container.innerHTML = '<p class="empty-state">No se requieren compras urgentes en este momento. Los niveles de inventario cubren la demanda estimada.</p>';
      return;
    }

    container.innerHTML = recs.map(r => {
      const prioClass = (r.priority || 'MEDIA').toLowerCase();
      const isNoBuy = r.action === 'NO_COMPRAR';

      return `
        <div class="recommendation-card ${prioClass}">
          <div class="rec-header">
            <div>
              <span class="badge ${isNoBuy ? 'badge-warning' : (r.priority === 'URGENTE' ? 'badge-danger' : 'badge-purple')}">
                ${r.priority} ${isNoBuy ? '⛔' : '🛒'}
              </span>
              <span class="rec-title" style="margin-left: 10px;">${r.product_name}</span>
            </div>
            <span class="badge badge-info">${r.category}</span>
          </div>

          <div class="rec-numbers">
            <span>Stock Actual en Tienda: <strong>${r.stock_actual} unid.</strong></span>
            <span>Stock Mínimo de Seguridad: <strong>${r.stock_minimo} unid.</strong></span>
            ${!isNoBuy ? `<span style="font-size: 0.95rem; color: #1e3a8a;">Sugerencia de Compra: <strong>${r.suggested_quantity} unidades</strong></span>` : ''}
          </div>

          <div class="rec-reason">
            ${r.natural_language_reason}
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    container.innerHTML = `<p class="empty-state" style="color: #dc2626;">Error generando recomendaciones: ${err.message}</p>`;
  }
}

async function retrainAiModel() {
  try {
    const res = await apiCall('/recommendations/retrain', { method: 'POST' });
    alert("¡Modelo reentrenado con éxito! Se han actualizado las ponderaciones de rotación y festividades.");
    await loadRecommendations();
  } catch (err) {
    alert(`Error reentrenando el modelo: ${err.message}`);
  }
}

// Formateador de moneda en pesos colombianos (COP)
function formatCurrency(amount) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0
  }).format(amount || 0);
}
