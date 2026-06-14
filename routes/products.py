import io
from flask import Blueprint, request, jsonify, render_template
from models import db, Product
from middleware import token_required, require_permission

products_bp = Blueprint('products', __name__)


# ── Serve page ────────────────────────────────────────
@products_bp.route('/products')
def products_page():
    return render_template('Products.html')


# ── GET /api/products  (all roles) ───────────────────
@products_bp.route('/api/products', methods=['GET'])
@token_required
@require_permission('products_read')
def get_products():
    category   = request.args.get('category')
    low_stock  = request.args.get('low_stock')
    search     = request.args.get('q', '').strip()

    query = Product.query
    if category:
        query = query.filter_by(category=category)
    if low_stock:
        query = query.filter(Product.quantity <= Product.reorder_level)
    if search:
        like = f'%{search}%'
        query = query.filter(Product.name.ilike(like) | Product.sku.ilike(like))

    products = query.order_by(Product.id.desc()).all()
    return jsonify([p.to_dict() for p in products]), 200


# ── POST /api/products  (Manager+) ───────────────────
@products_bp.route('/api/products', methods=['POST'])
@token_required
@require_permission('products_write')
def add_product():
    data = request.get_json()
    if not data.get('name') or not data.get('sku'):
        return jsonify({'error': 'Name and SKU are required.'}), 400
    if Product.query.filter_by(sku=data['sku'].strip().upper()).first():
        return jsonify({'error': 'SKU already exists.'}), 409

    p = Product(
        name          = data['name'].strip(),
        sku           = data['sku'].strip().upper(),
        category      = data.get('category', '').strip(),
        price         = float(data.get('price', 0)),
        quantity      = int(data.get('quantity', 0)),
        reorder_level = int(data.get('reorder_level', 10)),
        supplier      = data.get('supplier', '').strip()
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201


# ── PUT /api/products/<id>  (Manager+) ───────────────
@products_bp.route('/api/products/<int:pid>', methods=['PUT'])
@token_required
@require_permission('products_write')
def update_product(pid):
    p    = Product.query.get_or_404(pid)
    data = request.get_json()
    p.name          = data.get('name',          p.name).strip()
    p.sku           = data.get('sku',            p.sku).strip().upper()
    p.category      = data.get('category',      p.category)
    p.price         = float(data.get('price',   p.price))
    p.quantity      = int(data.get('quantity',  p.quantity))
    p.reorder_level = int(data.get('reorder_level', p.reorder_level))
    p.supplier      = data.get('supplier',      p.supplier)
    db.session.commit()
    return jsonify(p.to_dict()), 200


# ── DELETE /api/products/<id>  (Admin only) ──────────
@products_bp.route('/api/products/<int:pid>', methods=['DELETE'])
@token_required
@require_permission('products_delete')
def delete_product(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'message': f'Product "{p.name}" deleted.'}), 200


# ── POST /api/products/upload  (Manager+) ────────────
# Upload Excel/CSV to bulk-import products
@products_bp.route('/api/products/upload', methods=['POST'])
@token_required
@require_permission('upload')
def upload_products():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded.'}), 400

    file = request.files['file']
    filename = file.filename.lower()

    try:
        import pandas as pd

        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return jsonify({'error': 'Only .csv, .xlsx or .xls files are supported.'}), 400

        # Normalize column names — lowercase, strip spaces
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

        required_cols = ['name', 'sku']
        for col in required_cols:
            if col not in df.columns:
                return jsonify({'error': f'Missing required column: "{col}". File must have: name, sku, category, price, quantity, reorder_level, supplier'}), 400

        added = 0
        updated = 0
        errors = []

        for i, row in df.iterrows():
            try:
                sku  = str(row.get('sku', '')).strip().upper()
                name = str(row.get('name', '')).strip()
                if not sku or not name:
                    errors.append(f'Row {i+2}: name and sku are required.')
                    continue

                existing = Product.query.filter_by(sku=sku).first()
                if existing:
                    # Update existing
                    existing.name          = name
                    existing.category      = str(row.get('category', existing.category)).strip()
                    existing.price         = float(row.get('price', existing.price) or 0)
                    existing.quantity      = int(row.get('quantity', existing.quantity) or 0)
                    existing.reorder_level = int(row.get('reorder_level', existing.reorder_level) or 10)
                    existing.supplier      = str(row.get('supplier', existing.supplier)).strip()
                    updated += 1
                else:
                    p = Product(
                        name          = name,
                        sku           = sku,
                        category      = str(row.get('category', '')).strip(),
                        price         = float(row.get('price', 0) or 0),
                        quantity      = int(row.get('quantity', 0) or 0),
                        reorder_level = int(row.get('reorder_level', 10) or 10),
                        supplier      = str(row.get('supplier', '')).strip()
                    )
                    db.session.add(p)
                    added += 1
            except Exception as row_err:
                errors.append(f'Row {i+2}: {str(row_err)}')

        db.session.commit()
        return jsonify({
            'message': f'Import complete. {added} added, {updated} updated.',
            'added':   added,
            'updated': updated,
            'errors':  errors
        }), 200

    except ImportError:
        return jsonify({'error': 'pandas and openpyxl are required. Run: pip install pandas openpyxl'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
