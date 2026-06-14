//  reports.js  — Reports.html
Auth.guard();
initTopbar();

// Block low-privilege users
if (!canDo('reports_read')) {
  document.querySelector('.content').innerHTML =
    `<div style="padding:40px;text-align:center;color:var(--muted);font-size:13px">
      <div style="font-size:32px;margin-bottom:12px">🔒</div>
      You don't have permission to view reports.<br>
      <span style="font-size:11px">Analyst role or higher required.</span>
    </div>`;
}

const muted   = '#686b78';
const s2      = '#1c1e24';
const accent  = '#c8f04a';
const accent2 = '#4af0c8';
const accent3 = '#f04a7a';
const accent4 = '#f0a44a';
const COLORS  = [accent+'cc', accent2+'cc', accent4+'cc', accent3+'cc', '#a855f7cc', '#38bdf8cc'];

Chart.defaults.color       = muted;
Chart.defaults.font.family = "'DM Mono', monospace";
Chart.defaults.font.size   = 11;

// ── Load everything from single /api/reports endpoint ──
async function loadReports() {
  const res = await apiFetch('GET', '/api/reports');
  if (!res) return;
  if (!res.ok) {
    const err = await res.json();
    console.error('Reports error:', err.error);
    return;
  }
  const data = await res.json();

  renderStats(data);
  renderOrdersTrend(data);
  renderCategoryChart(data);
  renderTopProducts(data);
  renderStatusPie(data);
  renderForecastTable(data);
}

// ── KPI stats ─────────────────────────────
function renderStats(data) {
  document.getElementById('sRevenue').textContent  = '₹' + (data.total_revenue   || 0).toLocaleString();
  document.getElementById('sDelivered').textContent= data.orders_fulfilled || 0;
  document.getElementById('sAvg').textContent      = '₹' + (data.avg_order_value || 0).toLocaleString();
  document.getElementById('sLow').textContent      = data.low_stock || 0;
}

// ── Monthly orders trend (line) ───────────
function renderOrdersTrend(data) {
  const labels = data.monthly_labels?.length ? data.monthly_labels : ['Oct','Nov','Dec','Jan','Feb','Mar'];
  const values = data.monthly_values?.length ? data.monthly_values : [28, 35, 42, 31, 44, 48];
  new Chart(document.getElementById('ordersChart'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Orders', data: values,
        borderColor: accent, backgroundColor: accent + '18',
        borderWidth: 2, pointBackgroundColor: accent, pointRadius: 4,
        fill: true, tension: 0.4
      }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { x: { grid: { color: s2 } }, y: { grid: { color: s2 }, beginAtZero: true } }
    }
  });
}

// ── Category stock distribution (doughnut) ─
function renderCategoryChart(data) {
  const cats   = data.cat_stock || {};
  const labels = Object.keys(cats);
  const values = Object.values(cats);
  new Chart(document.getElementById('categoryChart'), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: COLORS.slice(0, labels.length),
        borderWidth: 0, hoverOffset: 6
      }]
    },
    options: {
      plugins: { legend: { position: 'right', labels: { boxWidth: 10, padding: 14, color: muted } } },
      cutout: '65%'
    }
  });
}

// ── Top products by revenue (horizontal bar) ─
function renderTopProducts(data) {
  const top    = data.top_products || [];
  const labels = top.map(p => p.product.length > 15 ? p.product.slice(0, 15) + '…' : p.product);
  const values = top.map(p => p.revenue);
  new Chart(document.getElementById('topProductsChart'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Revenue (₹)', data: values,
        backgroundColor: COLORS.slice(0, values.length),
        borderRadius: 5, borderSkipped: false
      }]
    },
    options: {
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: { x: { grid: { color: s2 } }, y: { grid: { color: 'transparent' } } }
    }
  });
}

// ── Order status split (pie) ──────────────
function renderStatusPie(data) {
  const byStatus = data.by_status || {};
  const labels   = Object.keys(byStatus);
  const values   = labels.map(k => byStatus[k].count || 0);
  new Chart(document.getElementById('statusChart'), {
    type: 'pie',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: [accent+'cc', accent2+'cc', accent4+'cc', accent3+'cc'],
        borderWidth: 0, hoverOffset: 6
      }]
    },
    options: {
      plugins: { legend: { position: 'right', labels: { boxWidth: 10, padding: 14, color: muted } } }
    }
  });
}

// ── Demand forecast table ─────────────────
function renderForecastTable(data) {
  const fc = data.forecast || [];
  document.getElementById('forecastBody').innerHTML = fc.map(f => `
    <tr>
      <td style="font-size:11px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.03)">
        <strong>${f.product}</strong>
        <span style="color:var(--muted);font-size:10px;margin-left:6px">${f.sku}</span>
      </td>
      <td style="font-size:11px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.03)">
        ${f.current_stock} units
      </td>
      <td style="font-size:11px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.03)">
        ${f.avg_demand} / order
      </td>
      <td style="font-size:11px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.03);color:var(--accent2)">
        ${f.predicted_demand} units
      </td>
      <td style="font-size:11px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.03);color:var(--accent)">
        ${f.suggested_order > 0 ? f.suggested_order + ' units' : '— sufficient'}
      </td>
      <td style="font-size:11px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.03)">
        ${f.needs_reorder
          ? '<span style="font-size:9px;padding:2px 7px;border-radius:3px;background:rgba(240,74,122,0.12);color:var(--accent3)">Reorder Now</span>'
          : '<span style="font-size:10px;color:var(--muted)">OK</span>'
        }
      </td>
    </tr>`
  ).join('') || '<tr><td colspan="6" style="color:var(--muted);font-size:11px;padding:16px">No forecast data yet. Add orders to generate predictions.</td></tr>';
}

loadReports();
