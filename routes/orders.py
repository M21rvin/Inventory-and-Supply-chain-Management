from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template
from models import db, Order, Product
from middleware import token_required, require_permission

orders_bp = Blueprint('orders', __name__)


def _next_order_id():
    last = Order.query.order_by(Order.id.desc()).first()
    if not last:
        return 'ORD-2241'
    try:
        num = int(last.order_id.split('-')[1]) + 1
    except (IndexError, ValueError):
        num = 2242
    return f'ORD-{num}'


def _deduct_stock(product_name, qty):
    """Deduct qty when order is Delivered. Returns (ok, msg)."""
    p = Product.query.filter(Product.name.ilike(product_name)).first()
    if not p:
        return True, 'Product not in inventory — stock unchanged.'
    if p.quantity < qty:
        return False, f'Insufficient stock. Available: {p.quantity}, requested: {qty}.'
    p.quantity -= qty
    return True, 'Stock updated.'


def _restore_stock(product_name, qty):
    """Restore stock when Delivered order is cancelled or deleted."""
    p = Product.query.filter(Product.name.ilike(product_name)).first()
    if p:
        p.quantity += qty


@orders_bp.route('/orders')
def orders_page():
    return render_template('Orders.html')


# ── GET /api/orders  (all roles) ─────────────────────
@orders_bp.route('/api/orders', methods=['GET'])
@token_required
@require_permission('orders_read')
def get_orders():
    status = request.args.get('status')
    search = request.args.get('q', '').strip()
    query  = Order.query
    if status:
        query = query.filter_by(status=status)
    if search:
        like  = f'%{search}%'
        query = query.filter(Order.order_id.ilike(like) | Order.product.ilike(like))
    orders = query.order_by(Order.id.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200


# ── POST /api/orders  (Employee+) ────────────────────
@orders_bp.route('/api/orders', methods=['POST'])
@token_required
@require_permission('orders_write')
def add_order():
    data    = request.get_json()
    product = data.get('product', '').strip()
    qty     = int(data.get('qty', 1))
    status  = data.get('status', 'Pending')

    if not product or qty < 1:
        return jsonify({'error': 'Product and valid quantity are required.'}), 400

    # Auto-deduct stock if placed as Delivered
    if status == 'Delivered':
        ok, msg = _deduct_stock(product, qty)
        if not ok:
            return jsonify({'error': msg}), 400

    o = Order(
        order_id   = _next_order_id(),
        product    = product,
        supplier   = data.get('supplier', '').strip(),
        customer   = data.get('customer', '').strip(),
        qty        = qty,
        price      = float(data.get('price', 0)),
        status     = status,
        order_date = data.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
    )
    db.session.add(o)
    db.session.commit()
    return jsonify(o.to_dict()), 201


# ── PUT /api/orders/<id>  (Employee+) ────────────────
@orders_bp.route('/api/orders/<int:oid>', methods=['PUT'])
@token_required
@require_permission('orders_write')
def update_order(oid):
    o          = Order.query.get_or_404(oid)
    data       = request.get_json()
    old_status = o.status
    new_status = data.get('status', o.status)
    qty        = int(data.get('qty', o.qty))

    # Status transition — stock adjustments
    if old_status != 'Delivered' and new_status == 'Delivered':
        ok, msg = _deduct_stock(o.product, qty)
        if not ok:
            return jsonify({'error': msg}), 400
    if old_status == 'Delivered' and new_status == 'Cancelled':
        _restore_stock(o.product, o.qty)

    o.product    = data.get('product',  o.product)
    o.supplier   = data.get('supplier', o.supplier)
    o.customer   = data.get('customer', o.customer)
    o.qty        = qty
    o.price      = float(data.get('price', o.price))
    o.status     = new_status
    o.order_date = data.get('date',     o.order_date)
    db.session.commit()
    return jsonify(o.to_dict()), 200


# ── DELETE /api/orders/<id>  (Manager+) ──────────────
@orders_bp.route('/api/orders/<int:oid>', methods=['DELETE'])
@token_required
@require_permission('orders_delete')
def delete_order(oid):
    o = Order.query.get_or_404(oid)
    if o.status == 'Delivered':
        _restore_stock(o.product, o.qty)
    db.session.delete(o)
    db.session.commit()
    return jsonify({'message': f'Order {o.order_id} deleted.'}), 200


# ── POST /api/orders/upload  (Manager+) ──────────────
@orders_bp.route('/api/orders/upload', methods=['POST'])
@token_required
@require_permission('upload')
def upload_orders():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded.'}), 400

    file     = request.files['file']
    filename = file.filename.lower()

    try:
        import pandas as pd

        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return jsonify({'error': 'Only .csv, .xlsx or .xls files are supported.'}), 400

        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

        if 'product' not in df.columns:
            return jsonify({'error': 'Missing required column: "product". Columns needed: product, supplier, customer, qty, price, status, date'}), 400

        added  = 0
        errors = []

        for i, row in df.iterrows():
            try:
                product = str(row.get('product', '')).strip()
                qty     = int(row.get('qty', 1) or 1)
                status  = str(row.get('status', 'Pending')).strip()

                if not product:
                    errors.append(f'Row {i+2}: product is required.')
                    continue

                if status == 'Delivered':
                    ok, msg = _deduct_stock(product, qty)
                    if not ok:
                        errors.append(f'Row {i+2}: {msg}')
                        continue

                o = Order(
                    order_id   = _next_order_id(),
                    product    = product,
                    supplier   = str(row.get('supplier', '')).strip(),
                    customer   = str(row.get('customer', '')).strip(),
                    qty        = qty,
                    price      = float(row.get('price', 0) or 0),
                    status     = status,
                    order_date = str(row.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))).strip()
                )
                db.session.add(o)
                added += 1
            except Exception as row_err:
                errors.append(f'Row {i+2}: {str(row_err)}')

        db.session.commit()
        return jsonify({
            'message': f'Import complete. {added} orders added.',
            'added':   added,
            'errors':  errors
        }), 200

    except ImportError:
        return jsonify({'error': 'pandas and openpyxl are required. Run: pip install pandas openpyxl'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
