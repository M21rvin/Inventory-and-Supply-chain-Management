from collections import defaultdict
from flask import Blueprint, request, jsonify, render_template
from models import Product, Supplier, Order
from middleware import token_required, require_permission

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
def reports_page():
    return render_template('Reports.html')


# ── GET /api/reports  (Analyst+) ─────────────────────
# Master endpoint — returns everything the Reports page needs
@reports_bp.route('/api/reports', methods=['GET'])
@token_required
@require_permission('reports_read')
def reports():
    products = Product.query.all()
    orders   = Order.query.all()

    # ── Revenue & order stats ──
    total_revenue = sum(o.qty * o.price for o in orders if o.status == 'Delivered')
    delivered     = [o for o in orders if o.status == 'Delivered']
    avg_order_val = round(sum(o.qty * o.price for o in orders) / len(orders), 2) if orders else 0
    low_stock_cnt = sum(1 for p in products if p.quantity <= p.reorder_level)

    # ── Revenue by status ──
    by_status = defaultdict(lambda: {'count': 0, 'revenue': 0})
    for o in orders:
        by_status[o.status]['count']   += 1
        by_status[o.status]['revenue'] += round(o.qty * o.price, 2)

    # ── Revenue by product ──
    by_product = defaultdict(lambda: {'qty': 0, 'revenue': 0, 'orders': 0})
    for o in orders:
        by_product[o.product]['qty']     += o.qty
        by_product[o.product]['revenue'] += round(o.qty * o.price, 2)
        by_product[o.product]['orders']  += 1

    top_products = sorted(
        [{'product': k, **v} for k, v in by_product.items()],
        key=lambda x: x['revenue'], reverse=True
    )[:6]

    # ── Monthly order trend (last 6 months) ──
    monthly = defaultdict(int)
    for o in orders:
        if o.order_date:
            month = o.order_date[:7]
            monthly[month] += 1
    monthly_sorted = sorted(monthly.items())[-6:]
    monthly_labels = [m[0] for m in monthly_sorted]
    monthly_values = [m[1] for m in monthly_sorted]

    # ── Category stock distribution ──
    cat_stock = defaultdict(int)
    for p in products:
        cat_stock[p.category] += p.quantity

    # ── Inventory report ──
    inventory = []
    for p in products:
        st = 'Out of Stock' if p.quantity == 0 else ('Low Stock' if p.quantity <= p.reorder_level else 'OK')
        inventory.append({
            **p.to_dict(),
            'stock_value':  round(p.quantity * p.price, 2),
            'stock_status': st
        })

    # ── Demand Forecast (Moving Average + trend factor) ──
    demand_history = defaultdict(list)
    for o in orders:
        demand_history[o.product.lower()].append(o.qty)

    forecast = []
    for p in products:
        history = demand_history.get(p.name.lower(), [])
        if not history:
            avg_demand, trend = 5, 1.0
        elif len(history) == 1:
            avg_demand, trend = history[0], 1.0
        else:
            avg_demand = sum(history) / len(history)
            mid        = len(history) // 2
            first_avg  = sum(history[:mid]) / mid if mid else avg_demand
            second_avg = sum(history[mid:]) / (len(history) - mid)
            trend      = max(0.5, min(2.0, second_avg / first_avg if first_avg > 0 else 1.0))

        predicted       = round(avg_demand * trend)
        suggested_order = max(0, predicted + p.reorder_level - p.quantity)
        needs_reorder   = p.quantity <= p.reorder_level

        forecast.append({
            'product':          p.name,
            'sku':              p.sku,
            'current_stock':    p.quantity,
            'reorder_level':    p.reorder_level,
            'avg_demand':       round(avg_demand, 1),
            'trend_factor':     round(trend, 2),
            'predicted_demand': predicted,
            'suggested_order':  suggested_order,
            'needs_reorder':    needs_reorder
        })
    forecast.sort(key=lambda x: (not x['needs_reorder'], x['current_stock']))

    return jsonify({
        # KPI stats
        'total_revenue':   round(total_revenue, 2),
        'orders_fulfilled': len(delivered),
        'avg_order_value': avg_order_val,
        'low_stock':       low_stock_cnt,
        'total_orders':    len(orders),
        # Charts
        'by_status':       {k: v for k, v in by_status.items()},
        'top_products':    top_products,
        'monthly_labels':  monthly_labels,
        'monthly_values':  monthly_values,
        'cat_stock':       dict(cat_stock),
        # Tables
        'inventory':       inventory,
        'forecast':        forecast,
    }), 200
