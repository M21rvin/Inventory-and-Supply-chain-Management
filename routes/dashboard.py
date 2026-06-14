from flask import Blueprint, jsonify, render_template
from models import Product, Supplier, Order
from middleware import token_required

dashboard_bp = Blueprint('dashboard', __name__)


# ── Serve dashboard page ──────────────────────────────
@dashboard_bp.route('/dashboard')
def dashboard_page():
    return render_template('index.html')


# ── GET /api/dashboard  (all roles) ──────────────────
@dashboard_bp.route('/api/dashboard')
@token_required
def dashboard_data():
    products  = Product.query.all()
    orders    = Order.query.all()

    # KPI counts
    low_stock = sum(1 for p in products if p.quantity <= p.reorder_level)
    delivered = [o for o in orders if o.status == 'Delivered']
    revenue   = sum(o.qty * o.price for o in delivered)

    # Stock by category (for doughnut chart)
    cat_stock = {}
    for p in products:
        cat_stock[p.category] = cat_stock.get(p.category, 0) + p.quantity

    # Recent products (last 5)
    recent_products = Product.query.order_by(Product.id.desc()).limit(5).all()

    # Recent orders (last 5)
    recent_orders = Order.query.order_by(Order.id.desc()).limit(5).all()

    # Monthly order counts (last 6 months — approximate from order_date string)
    from collections import defaultdict
    monthly = defaultdict(int)
    for o in orders:
        if o.order_date:
            month = o.order_date[:7]   # 'YYYY-MM'
            monthly[month] += 1
    monthly_sorted = sorted(monthly.items())[-6:]
    monthly_labels = [m[0] for m in monthly_sorted]
    monthly_values = [m[1] for m in monthly_sorted]

    return jsonify({
        'products':        Product.query.count(),
        'suppliers':       Supplier.query.count(),
        'orders':          Order.query.count(),
        'low_stock':       low_stock,
        'revenue':         round(revenue, 2),
        'cat_stock':       cat_stock,
        'monthly_labels':  monthly_labels,
        'monthly_values':  monthly_values,
        'recent_products': [p.to_dict() for p in recent_products],
        'recent_orders':   [o.to_dict() for o in recent_orders],
    }), 200
