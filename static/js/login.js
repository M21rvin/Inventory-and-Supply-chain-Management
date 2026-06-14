// ═══════════════════════════════════════
//  login.js  — Auth: Login + Register
//  Drop into login.html before </body>
// ═══════════════════════════════════════

const api = window.API_BASE || '';  // '' = same origin (Flask serves templates)

// ── If already logged in skip to dashboard ──
if (localStorage.getItem('ims_token')) {
  window.location.href = '/dashboard';
}

// ── Tab switcher ──────────────────────────
function showTab(tab) {
  const isLogin = tab === 'login';
  document.getElementById('loginTab').style.display    = isLogin ? 'block' : 'none';
  document.getElementById('registerTab').style.display = isLogin ? 'none'  : 'block';
  const lb = document.getElementById('tabLoginBtn');
  const rb = document.getElementById('tabRegisterBtn');
  lb.style.background = isLogin ? 'var(--accent)' : 'transparent';
  lb.style.color      = isLogin ? 'var(--bg)'     : 'var(--muted)';
  lb.style.fontWeight = isLogin ? '600'            : '400';
  rb.style.background = isLogin ? 'transparent'   : 'var(--accent)';
  rb.style.color      = isLogin ? 'var(--muted)'  : 'var(--bg)';
  rb.style.fontWeight = isLogin ? '400'            : '600';
  clearMsgs();
}

function showErr(msg) {
  const e = document.getElementById('errorMsg');
  e.textContent = msg; e.style.display = 'block';
  document.getElementById('successMsg').style.display = 'none';
}
function showOk(msg) {
  const e = document.getElementById('successMsg');
  e.textContent = msg; e.style.display = 'block';
  document.getElementById('errorMsg').style.display = 'none';
}
function clearMsgs() {
  document.getElementById('errorMsg').style.display   = 'none';
  document.getElementById('successMsg').style.display = 'none';
}

// ── Password toggle ───────────────────────
document.getElementById('togglePw').addEventListener('click', () => {
  const p = document.getElementById('password');
  p.type = p.type === 'password' ? 'text' : 'password';
});

// ── LOGIN ─────────────────────────────────
document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  clearMsgs();
  const btn = document.getElementById('loginBtn');
  const txt = document.getElementById('btnText');
  btn.classList.add('loading'); txt.textContent = 'Logging in...';

  try {
    const res  = await fetch(`${API}/login`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        email:    document.getElementById('email').value.trim(),
        password: document.getElementById('password').value
      })
    });
    const data = await res.json();

    if (data.success) {
      localStorage.setItem('ims_token', data.token);
      localStorage.setItem('ims_user',  JSON.stringify(data.user));
      window.location.href = '/dashboard';
    } else {
      showErr(data.message || 'Login failed.');
      btn.classList.remove('loading'); txt.textContent = 'Login';
    }
  } catch (err) {
    showErr('Cannot connect to server. Is Flask running?');
    btn.classList.remove('loading'); txt.textContent = 'Login';
  }
});

// ── REGISTER ──────────────────────────────
document.getElementById('registerForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  clearMsgs();

  const pass    = document.getElementById('rPassword').value;
  const confirm = document.getElementById('rConfirm').value;
  if (pass.length < 6)   { showErr('Password must be at least 6 characters.');  return; }
  if (pass !== confirm)  { showErr('Passwords do not match.'); return; }

  try {
    const res  = await fetch(`${API}/register`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        name:     document.getElementById('rName').value.trim(),
        email:    document.getElementById('rEmail').value.trim(),
        password: pass,
        confirm:  confirm,
        role:     document.getElementById('rRole').value,
        dept:     document.getElementById('rDept').value.trim()
      })
    });
    const data = await res.json();

    if (data.success) {
      showOk('Account created! Redirecting to login...');
      setTimeout(() => showTab('login'), 1800);
    } else {
      showErr(data.message || 'Registration failed.');
    }
  } catch (err) {
    showErr('Cannot connect to server.');
  }
});
