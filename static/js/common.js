// ═══════════════════════════════════════
//  common.js — shared auth + API helpers
//  Include in every page before page-specific JS
// ═══════════════════════════════════════
console.log("hello")
const API = window.API_BASE || ''

// ── Token helpers ─────────────────────────
const Auth = {
  token:   ()  => localStorage.getItem('ims_token'),
  user:    ()  => JSON.parse(localStorage.getItem('ims_user') || 'null'),
  headers: ()  => ({ 'Content-Type': 'application/json', 'Authorization': `Bearer ${Auth.token()}` }),
  guard:   ()  => { if (!Auth.token()) { window.location.href = '/'; return false; } return true; },
  logout:  async () => {
    await fetch(`${API}/logout`, { method: 'POST', headers: Auth.headers() }).catch(() => {});
    localStorage.removeItem('ims_token');
    localStorage.removeItem('ims_user');
    window.location.href = '/';
  }
};

// ── RBAC — role levels ────────────────────
const ROLE_LEVELS = {
  'Admin': 5, 'Manager': 4, 'Analyst': 3, 'Warehouse Staff': 2, 'Employee': 1
};
function canDo(permission) {
  const required = {
    products_write: 4, products_delete: 5,
    suppliers_read: 3, suppliers_write: 4, suppliers_delete: 5,
    orders_delete:  4, reports_read: 3, upload: 4, users: 5
  };
  const user  = Auth.user();
  const level = ROLE_LEVELS[user?.role] || 0;
  return level >= (required[permission] || 1);
}

// ── Fetch wrapper — auto 401 redirect ────
async function apiFetch(method, path, body) {
  const opts = { method, headers: Auth.headers() };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${API}${path}`, opts);
  if (res.status === 401) { Auth.guard(); return null; }
  return res;
}

// ── Init topbar (date + avatar) ───────────
function initTopbar() {
  const dateEl = document.getElementById('dateDisplay');
  if (dateEl) dateEl.textContent = new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });

  const user   = Auth.user();
  const initEl = document.getElementById('avatarInitial');
  if (initEl && user) initEl.textContent = user.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

  const menuName = document.getElementById('menuName');
  const menuRole = document.getElementById('menuRole');
  if (menuName && user) menuName.textContent = user.name;
  if (menuRole && user) menuRole.textContent  = user.role;

  // Avatar dropdown toggle
  const avatarEl = document.getElementById('avatarEl');
  if (avatarEl) {
    avatarEl.addEventListener('click', (e) => {
      e.stopPropagation();
      const m = document.getElementById('avatarMenu');
      if (m) m.style.display = m.style.display === 'none' ? 'block' : 'none';
    });
    document.addEventListener('click', () => {
      const m = document.getElementById('avatarMenu');
      if (m) m.style.display = 'none';
    });
  }

  // Logout buttons
  ['logoutBtn', 'menuLogout'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('click', Auth.logout);
  });

  // Hide UI elements the current user can't access
  applyRBAC();
}

// ── Apply RBAC to DOM elements ────────────
// Add data-permission="products_write" to any element you want hidden by role
function applyRBAC() {
  document.querySelectorAll('[data-permission]').forEach(el => {
    const perm = el.getAttribute('data-permission');
    if (!canDo(perm)) el.style.display = 'none';
  });

  // Hide suppliers link for Employee / Warehouse Staff
  if (!canDo('suppliers_read')) {
    document.querySelectorAll('a[href*="suppliers"], a[href*="Suppliers"]').forEach(el => {
      el.closest('li')?.style.setProperty('display', 'none');
    });
  }
  // Hide reports link for Employee / Warehouse Staff
  if (!canDo('reports_read')) {
    document.querySelectorAll('a[href*="reports"], a[href*="Reports"]').forEach(el => {
      el.closest('li')?.style.setProperty('display', 'none');
    });
  }
}
