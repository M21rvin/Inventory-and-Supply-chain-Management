// ═══════════════════════════════════════
//  dashboard.js  — index.html
// ═══════════════════════════════════════

Auth.guard();
initTopbar();

const dotMap = { Delivered: 'green', Processing: 'blue', Pending: 'yellow', Cancelled: 'red' };

function stockStatus(q, r) {
  if (q === 0)    return { label: 'Out',      cls: 'low' };
  if (q <= r)     return { label: 'Low',      cls: 'warn' };
  return                  { label: 'In Stock', cls: 'ok' };
}

async function loadDashboard() {
  const res  = await apiFetch('GET', '/api/dashboard');
  if (!res) return;
  const data = await res.json();

  // ── KPI Cards ──
  document.getElementById('statProducts').textContent  = data.products;
  document.getElementById('statSuppliers').textContent = data.suppliers;
  document.getElementById('statOrders').textContent    = data.orders;
  document.getElementById('statLow').textContent       = data.low_stock;

  // ── Recent Products table ──
  document.getElementById('recentProducts').innerHTML = (data.recent_products || []).map(p => {
    const st = stockStatus(p.quantity, p.reorder_level);
    return `<tr>
      <td><strong>${p.name}</strong></td>
      <td class="sku">${p.sku}</td>
      <td>${p.quantity}</td>
      <td><span class="badge ${st.cls}">${st.label}</span></td>
    </tr>`;
  }).join('') || '<tr><td colspan="4" style="color:var(--muted);font-size:11px">No products yet.</td></tr>';

  // ── Recent Orders list ──
  document.getElementById('recentOrders').innerHTML = (data.recent_orders || []).map(o => `
    <div class="activity-item">
      <div class="activity-dot ${dotMap[o.status] || 'green'}"></div>
      <div>
        <div class="activity-text">${o.order_id} — ${o.product}</div>
        <div class="activity-time">${o.status} · ${o.date || ''}</div>
      </div>
    </div>`).join('') || '<div class="activity-item"><div class="activity-dot green"></div><div><div class="activity-text">No orders yet.</div></div></div>';

  // ── Charts ──
  const muted = '#686b78', s2 = '#1c1e24';
  Chart.defaults.color       = muted;
  Chart.defaults.font.family = "'DM Mono', monospace";
  Chart.defaults.font.size   = 11;

  // Sales trend line chart
  const labels = data.monthly_labels?.length ? data.monthly_labels : ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'];
  const values = data.monthly_values?.length ? data.monthly_values : [28, 35, 42, 31, 44, 48];
  new Chart(document.getElementById('salesChart'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Orders', data: values,
        borderColor: '#c8f04a', backgroundColor: 'rgba(200,240,74,0.08)',
        borderWidth: 2, pointBackgroundColor: '#c8f04a', pointRadius: 4,
        fill: true, tension: 0.4
      }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { x: { grid: { color: s2 } }, y: { grid: { color: s2 }, beginAtZero: true } },
      responsive: true, maintainAspectRatio: false
    }
  });

  // Stock distribution doughnut
  const cats   = data.cat_stock || {};
  const colors = ['#c8f04acc', '#4af0c8cc', '#f0a44acc', '#f04a7acc', '#a855f7cc', '#38bdf8cc'];
  new Chart(document.getElementById('stockChart'), {
    type: 'doughnut',
    data: {
      labels: Object.keys(cats),
      datasets: [{ data: Object.values(cats), backgroundColor: colors.slice(0, Object.keys(cats).length), borderWidth: 0, hoverOffset: 6 }]
    },
    options: {
      plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, padding: 10, color: muted } } },
      cutout: '62%', responsive: true, maintainAspectRatio: false
    }
  });
}

loadDashboard();
