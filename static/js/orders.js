// ═══════════════════════════════════════
//  orders.js  — Orders.html
// ═══════════════════════════════════════

Auth.guard();
initTopbar();

let orders = [], allProducts = [], deleteId = null;

const statusMap = {
  Pending:    { cls: 'warn' },
  Processing: { cls: 'blue' },
  Delivered:  { cls: 'ok'   },
  Cancelled:  { cls: 'low'  }
};

// ── Load orders + products ────────────────
async function load() {
  const [oRes, pRes] = await Promise.all([
    apiFetch('GET', '/api/orders'),
    apiFetch('GET', '/api/products')
  ]);
  if (!oRes || !pRes) return;
  orders      = await oRes.json();
  allProducts = await pRes.json();
  populateProductDropdown();
  render();
}

// ── Populate product <select> ─────────────
function populateProductDropdown() {
  const sel = document.getElementById('fProduct');
  if (!sel) return;
  sel.innerHTML = '<option value="">Select product...</option>' +
    allProducts.map(p =>
      `<option value="${p.id}" data-price="${p.price}" data-supplier="${p.supplier || ''}">${p.name} (Stock: ${p.quantity})</option>`
    ).join('');
}

// ── Auto-fill price + supplier on select ──
window.autoFill = function () {
  const sel = document.getElementById('fProduct');
  const opt = sel.options[sel.selectedIndex];
  if (opt && opt.value) {
    document.getElementById('fPrice').value    = opt.dataset.price    || '';
    document.getElementById('fSupplier').value = opt.dataset.supplier || '';
  }
};

// ── Render table ──────────────────────────
function render() {
  const search   = document.getElementById('searchInput').value.toLowerCase();
  const filterS  = document.getElementById('filterStatus').value;
  const canDelete = canDo('orders_delete');

  const filtered = orders.filter(o =>
    ((o.order_id || '').toLowerCase().includes(search) ||
     (o.product  || '').toLowerCase().includes(search)) &&
    (!filterS || o.status === filterS)
  );

  document.getElementById('tableBody').innerHTML = filtered.map(o => {
    const st = statusMap[o.status] || { cls: 'ok' };
    return `<tr>
      <td class="sku">${o.order_id}</td>
      <td><strong>${o.product}</strong></td>
      <td class="sku">${o.supplier  || '—'}</td>
      <td class="sku">${o.customer  || '—'}</td>
      <td>${o.qty}</td>
      <td><strong>₹${((o.qty || 0) * (o.price || 0)).toLocaleString()}</strong></td>
      <td class="sku">${o.date || '—'}</td>
      <td><span class="badge ${st.cls}">${o.status}</span></td>
      <td>
        <div class="action-btns">
          ${canDelete ? `<button class="btn-icon del" onclick="openDelete(${o.id},'${o.order_id}')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
              <path d="M10 11v6"/><path d="M14 11v6"/>
            </svg>
          </button>` : ''}
        </div>
      </td>
    </tr>`;
  }).join('') || `<tr><td colspan="9" style="color:var(--muted);font-size:11px;padding:20px">No orders found.</td></tr>`;
}

// ── Modal helpers ─────────────────────────
function openModal() {
  document.getElementById('fProduct').value  = '';
  document.getElementById('fSupplier').value = '';
  document.getElementById('fQty').value      = '';
  document.getElementById('fPrice').value    = '';
  document.getElementById('fStatus').value   = 'Pending';
  document.getElementById('fCustomer').value = '';
  document.getElementById('fDate').value     = new Date().toISOString().split('T')[0];
  document.getElementById('formError').style.display = 'none';
  document.getElementById('modalOverlay').classList.add('active');
}
function closeModal()  { document.getElementById('modalOverlay').classList.remove('active'); }
function openDelete(id, orderId) {
  if (!canDo('orders_delete')) { alert('Manager role required to delete orders.'); return; }
  deleteId = id;
  document.getElementById('deleteOrderId').textContent = orderId;
  document.getElementById('deleteOverlay').classList.add('active');
}
function closeDelete() { document.getElementById('deleteOverlay').classList.remove('active'); }

// ── Save Order ────────────────────────────
document.getElementById('saveOrder').addEventListener('click', async () => {
  const sel      = document.getElementById('fProduct');
  const prodName = sel.options[sel.selectedIndex]?.text?.split(' (Stock')[0] || '';
  const qty      = parseInt(document.getElementById('fQty').value);
  const price    = parseFloat(document.getElementById('fPrice').value);
  const err      = document.getElementById('formError');

  if (!prodName || isNaN(qty) || isNaN(price) || qty < 1) {
    err.textContent = 'Product, quantity and price are required.';
    err.style.display = 'block';
    return;
  }

  const body = {
    product:  prodName,
    supplier: document.getElementById('fSupplier').value.trim(),
    customer: document.getElementById('fCustomer').value.trim(),
    qty,
    price,
    status:   document.getElementById('fStatus').value,
    date:     document.getElementById('fDate').value
  };

  const res  = await apiFetch('POST', '/api/orders', body);
  if (!res) return;
  const data = await res.json();
  if (!res.ok) {
    err.textContent = data.error || 'Failed to save order.';
    err.style.display = 'block';
    return;
  }
  closeModal();
  load();
});

// ── Confirm Delete ────────────────────────
document.getElementById('confirmDelete').addEventListener('click', async () => {
  const res = await apiFetch('DELETE', `/api/orders/${deleteId}`);
  if (res) { closeDelete(); load(); }
});

// ── Excel Upload (Manager+) ───────────────
if (canDo('upload')) {
  const toolbar = document.querySelector('.toolbar-right');
  if (toolbar) {
    const uploadBtn = document.createElement('button');
    uploadBtn.className   = 'btn-add';
    uploadBtn.style.background = 'var(--accent2)';
    uploadBtn.style.marginLeft = '4px';
    uploadBtn.textContent = '↑ Import Excel/CSV';
    uploadBtn.addEventListener('click', () => document.getElementById('ordersFileInput').click());
    toolbar.appendChild(uploadBtn);

    const fileInput = document.createElement('input');
    fileInput.type    = 'file';
    fileInput.id      = 'ordersFileInput';
    fileInput.accept  = '.xlsx,.xls,.csv';
    fileInput.style.display = 'none';
    fileInput.addEventListener('change', uploadExcel);
    toolbar.appendChild(fileInput);
  }
}

async function uploadExcel(e) {
  const file = e.target.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);
  const res  = await fetch('/api/orders/upload', {
    method:  'POST',
    headers: { 'Authorization': `Bearer ${Auth.token()}` },
    body:    formData
  });
  const data = await res.json();
  if (res.ok) {
    alert(`${data.message}\n${data.errors?.length ? 'Errors:\n' + data.errors.join('\n') : ''}`);
    load();
  } else {
    alert('Upload failed: ' + (data.error || 'Unknown error'));
  }
  e.target.value = '';
}

// ── Event listeners ───────────────────────
document.getElementById('openModal').addEventListener('click',    openModal);
document.getElementById('closeModal').addEventListener('click',   closeModal);
document.getElementById('cancelModal').addEventListener('click',  closeModal);
document.getElementById('closeDelete').addEventListener('click',  closeDelete);
document.getElementById('cancelDelete').addEventListener('click', closeDelete);
document.getElementById('searchInput').addEventListener('input',  render);
document.getElementById('filterStatus').addEventListener('change',render);

load();
