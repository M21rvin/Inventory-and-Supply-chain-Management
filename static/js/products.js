//  products.js  — Products.html
Auth.guard();
initTopbar();

let products = [], editId = null, deleteId = null;

function stockStatus(q, r) {
  if (q === 0)  return { label: 'Out',      cls: 'low' };
  if (q <= r)   return { label: 'Low',      cls: 'warn' };
  return               { label: 'In Stock', cls: 'ok' };
}

// ── Load products from API ────────────────
async function load() {
  const res = await apiFetch('GET', '/api/products');
  if (!res) return;
  if (!res.ok) { console.error('Failed to load products'); return; }
  products = await res.json();
  render();
}

// ── Render table ──────────────────────────
function render() {
  const search  = document.getElementById('searchInput').value.toLowerCase();
  const filterS = document.getElementById('filterStatus').value;
  const filterC = document.getElementById('filterCategory').value;

  const filtered = products.filter(p => {
    const st = stockStatus(p.quantity, p.reorder_level);
    return (
      (p.name.toLowerCase().includes(search) || p.sku.toLowerCase().includes(search)) &&
      (!filterS || st.label === filterS) &&
      (!filterC || p.category === filterC)
    );
  });

  const canWrite  = canDo('products_write');
  const canDelete = canDo('products_delete');

  document.getElementById('tableBody').innerHTML = filtered.map(p => {
    const st    = stockStatus(p.quantity, p.reorder_level);
    const alert = p.quantity <= p.reorder_level ? '⚠️ ' : '';
    const actions = `
      <div class="action-btns">
        ${canWrite  ? `<button class="btn-icon edit" onclick="openEdit(${p.id})"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>` : ''}
        ${canDelete ? `<button class="btn-icon del" onclick="openDelete(${p.id},'${p.name.replace(/'/g,"\\'")}')"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg></button>` : ''}
      </div>`;
    return `<tr>
      <td><strong>${alert}${p.name}</strong></td>
      <td class="sku">${p.sku}</td>
      <td><span class="cat-badge">${p.category}</span></td>
      <td>₹${(p.price || 0).toLocaleString()}</td>
      <td>${p.quantity}</td>
      <td style="color:var(--muted)">${p.reorder_level || 10}</td>
      <td class="sku">${p.supplier || '—'}</td>
      <td><span class="badge ${st.cls}">${st.label}</span></td>
      <td>${actions}</td>
    </tr>`;
  }).join('') || `<tr><td colspan="9" style="color:var(--muted);font-size:11px;padding:20px">No products found.</td></tr>`;

  // Show/hide Add Product button based on role
  const addBtn = document.getElementById('openModal');
  if (addBtn) addBtn.style.display = canDo('products_write') ? '' : 'none';
}

// ── Modal helpers ─────────────────────────
function openModal() {
  if (!canDo('products_write')) { alert('Access denied. Manager role required.'); return; }
  editId = null;
  document.getElementById('modalTitle').textContent = 'Add Product';
  ['fName','fSku','fPrice','fStock','fReorder','fSupplier'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('fCategory').value = 'Audio';
  document.getElementById('formError').style.display = 'none';
  document.getElementById('modalOverlay').classList.add('active');
}
function openEdit(id) {
  if (!canDo('products_write')) { alert('Access denied.'); return; }
  const p = products.find(x => x.id === id); editId = id;
  document.getElementById('modalTitle').textContent = 'Edit Product';
  document.getElementById('fName').value     = p.name;
  document.getElementById('fSku').value      = p.sku;
  document.getElementById('fCategory').value = p.category;
  document.getElementById('fPrice').value    = p.price;
  document.getElementById('fStock').value    = p.quantity;
  document.getElementById('fReorder').value  = p.reorder_level || 10;
  document.getElementById('fSupplier').value = p.supplier;
  document.getElementById('formError').style.display = 'none';
  document.getElementById('modalOverlay').classList.add('active');
}
function closeModal()  { document.getElementById('modalOverlay').classList.remove('active'); }
function openDelete(id, name) {
  if (!canDo('products_delete')) { alert('Access denied. Admin role required to delete products.'); return; }
  deleteId = id;
  document.getElementById('deleteProductName').textContent = name;
  document.getElementById('deleteOverlay').classList.add('active');
}
function closeDelete() { document.getElementById('deleteOverlay').classList.remove('active'); }

// ── Save (Add/Edit) ───────────────────────
document.getElementById('saveProduct').addEventListener('click', async () => {
  const body = {
    name:          document.getElementById('fName').value.trim(),
    sku:           document.getElementById('fSku').value.trim(),
    category:      document.getElementById('fCategory').value,
    price:         parseFloat(document.getElementById('fPrice').value),
    quantity:      parseInt(document.getElementById('fStock').value),
    reorder_level: parseInt(document.getElementById('fReorder').value) || 10,
    supplier:      document.getElementById('fSupplier').value.trim()
  };
  const err = document.getElementById('formError');
  if (!body.name || !body.sku || isNaN(body.price) || isNaN(body.quantity)) {
    err.textContent = 'Name, SKU, Price and Quantity are required.'; err.style.display = 'block'; return;
  }
  const url    = editId ? `/api/products/${editId}` : '/api/products';
  const method = editId ? 'PUT' : 'POST';
  const res    = await apiFetch(method, url, body);
  if (!res) return;
  const data = await res.json();
  if (!res.ok) { err.textContent = data.error || 'Save failed.'; err.style.display = 'block'; return; }
  closeModal(); load();
});

// ── Confirm Delete ────────────────────────
document.getElementById('confirmDelete').addEventListener('click', async () => {
  const res = await apiFetch('DELETE', `/api/products/${deleteId}`);
  if (res) { closeDelete(); load(); }
});

// ── Excel Upload ──────────────────────────
// Inject upload button next to Add Product if role allows
if (canDo('upload')) {
  const toolbar = document.querySelector('.toolbar-right');
  if (toolbar) {
    const uploadBtn = document.createElement('button');
    uploadBtn.className = 'btn-add';
    uploadBtn.style.background = 'var(--accent2)';
    uploadBtn.style.marginLeft = '4px';
    uploadBtn.textContent = '↑ Import Excel/CSV';
    uploadBtn.addEventListener('click', () => document.getElementById('excelFileInput').click());
    toolbar.appendChild(uploadBtn);

    const fileInput = document.createElement('input');
    fileInput.type = 'file'; fileInput.id = 'excelFileInput';
    fileInput.accept = '.xlsx,.xls,.csv'; fileInput.style.display = 'none';
    fileInput.addEventListener('change', uploadExcel);
    toolbar.appendChild(fileInput);
  }
}

async function uploadExcel(e) {
  const file = e.target.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch('/api/products/upload', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${Auth.token()}` },
    body: formData
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
document.getElementById('openModal').addEventListener('click', openModal);
document.getElementById('closeModal').addEventListener('click', closeModal);
document.getElementById('cancelModal').addEventListener('click', closeModal);
document.getElementById('closeDelete').addEventListener('click', closeDelete);
document.getElementById('cancelDelete').addEventListener('click', closeDelete);
document.getElementById('searchInput').addEventListener('input', render);
document.getElementById('filterStatus').addEventListener('change', render);
document.getElementById('filterCategory').addEventListener('change', render);

load();
