//  suppliers.js  — Suppliers.html
Auth.guard();
initTopbar();

// Block low-privilege users from this page entirely
if (!canDo('suppliers_read')) {
  document.querySelector('.content').innerHTML =
    `<div style="padding:40px;text-align:center;color:var(--muted);font-size:13px">
      <div style="font-size:32px;margin-bottom:12px">🔒</div>
      You don't have permission to view suppliers.<br>
      <span style="font-size:11px">Analyst role or higher required.</span>
    </div>`;
}

let suppliers = [], editId = null, deleteId = null;
const colors  = ['var(--accent)', 'var(--accent2)', 'var(--accent4)', 'var(--accent3)'];
const initials = n => n.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

// ── Load ──────────────────────────────────
async function load() {
  const res = await apiFetch('GET', '/api/suppliers');
  if (!res || !res.ok) return;
  suppliers = await res.json();
  render();
}

// ── Render cards ──────────────────────────
function render() {
  const search    = document.getElementById('searchInput').value.toLowerCase();
  const canWrite  = canDo('suppliers_write');
  const canDelete = canDo('suppliers_delete');

  const filtered = suppliers.filter(s =>
    s.name.toLowerCase().includes(search) ||
    (s.contact || '').toLowerCase().includes(search) ||
    (s.city    || '').toLowerCase().includes(search)
  );

  document.getElementById('supplierGrid').innerHTML = filtered.map((s, i) => `
    <div class="supplier-card" style="animation-delay:${i * 0.05}s">
      <div class="supplier-card-top">
        <div class="supplier-avatar" style="background:${colors[i % colors.length]}20;color:${colors[i % colors.length]}">${initials(s.name)}</div>
        <div class="action-btns">
          ${canWrite  ? `<button class="btn-icon edit" onclick="openEdit(${s.id})">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>` : ''}
          ${canDelete ? `<button class="btn-icon del" onclick="openDelete(${s.id},'${s.name.replace(/'/g,"\\'")}')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
          </button>` : ''}
        </div>
      </div>
      <div class="supplier-name">${s.name}</div>
      <div class="supplier-contact">${s.contact || '—'}</div>
      <div class="supplier-meta">
        <div class="meta-row"><span>📧</span> ${s.email    || '—'}</div>
        <div class="meta-row"><span>📞</span> ${s.phone    || '—'}</div>
        <div class="meta-row"><span>📦</span> ${s.category || '—'}</div>
        <div class="meta-row"><span>📍</span> ${s.city     || '—'}</div>
      </div>
    </div>`
  ).join('') || '<p style="color:var(--muted);font-size:11px">No suppliers found.</p>';

  // Show/hide Add button by role
  const addBtn = document.getElementById('openModal');
  if (addBtn) addBtn.style.display = canWrite ? '' : 'none';
}

// ── Modal helpers ─────────────────────────
function openModal() {
  if (!canDo('suppliers_write')) { alert('Manager role required to add suppliers.'); return; }
  editId = null;
  document.getElementById('modalTitle').textContent = 'Add Supplier';
  ['fName','fContact','fEmail','fPhone','fCategory','fCity'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('modalOverlay').classList.add('active');
}
function openEdit(id) {
  if (!canDo('suppliers_write')) { alert('Access denied.'); return; }
  const s = suppliers.find(x => x.id === id); editId = id;
  document.getElementById('modalTitle').textContent = 'Edit Supplier';
  document.getElementById('fName').value     = s.name;
  document.getElementById('fContact').value  = s.contact;
  document.getElementById('fEmail').value    = s.email;
  document.getElementById('fPhone').value    = s.phone;
  document.getElementById('fCategory').value = s.category;
  document.getElementById('fCity').value     = s.city;
  document.getElementById('modalOverlay').classList.add('active');
}
function closeModal()  { document.getElementById('modalOverlay').classList.remove('active'); }
function openDelete(id, name) {
  if (!canDo('suppliers_delete')) { alert('Admin role required to delete suppliers.'); return; }
  deleteId = id;
  document.getElementById('deleteSupplierName').textContent = name;
  document.getElementById('deleteOverlay').classList.add('active');
}
function closeDelete() { document.getElementById('deleteOverlay').classList.remove('active'); }

// ── Save ──────────────────────────────────
document.getElementById('saveSupplier').addEventListener('click', async () => {
  const body = {
    name:     document.getElementById('fName').value.trim(),
    contact:  document.getElementById('fContact').value.trim(),
    email:    document.getElementById('fEmail').value.trim(),
    phone:    document.getElementById('fPhone').value.trim(),
    category: document.getElementById('fCategory').value.trim(),
    city:     document.getElementById('fCity').value.trim()
  };
  if (!body.name) return;
  const url    = editId ? `/api/suppliers/${editId}` : '/api/suppliers';
  const method = editId ? 'PUT' : 'POST';
  const res    = await apiFetch(method, url, body);
  if (!res) return;
  const data = await res.json();
  if (!res.ok) { alert(data.error || 'Save failed.'); return; }
  closeModal(); load();
});

// ── Confirm Delete ────────────────────────
document.getElementById('confirmDelete').addEventListener('click', async () => {
  const res = await apiFetch('DELETE', `/api/suppliers/${deleteId}`);
  if (res) { closeDelete(); load(); }
});

// ── Event listeners ───────────────────────
document.getElementById('openModal').addEventListener('click',   openModal);
document.getElementById('closeModal').addEventListener('click',  closeModal);
document.getElementById('cancelModal').addEventListener('click', closeModal);
document.getElementById('closeDelete').addEventListener('click', closeDelete);
document.getElementById('cancelDelete').addEventListener('click',closeDelete);
document.getElementById('searchInput').addEventListener('input', render);

load();
