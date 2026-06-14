from flask import Blueprint, request, jsonify, render_template
from models import db, Supplier
from middleware import token_required, require_permission

suppliers_bp = Blueprint('suppliers', __name__)


@suppliers_bp.route('/suppliers')
def suppliers_page():
    return render_template('Suppliers.html')


# ── GET /api/suppliers  (Analyst+) ───────────────────
@suppliers_bp.route('/api/suppliers', methods=['GET'])
@token_required
@require_permission('suppliers_read')
def get_suppliers():
    search = request.args.get('q', '').strip()
    query  = Supplier.query
    if search:
        like  = f'%{search}%'
        query = query.filter(
            Supplier.name.ilike(like) |
            Supplier.city.ilike(like) |
            Supplier.category.ilike(like)
        )
    suppliers = query.order_by(Supplier.name).all()
    return jsonify([s.to_dict() for s in suppliers]), 200


# ── POST /api/suppliers  (Manager+) ──────────────────
@suppliers_bp.route('/api/suppliers', methods=['POST'])
@token_required
@require_permission('suppliers_write')
def add_supplier():
    data = request.get_json()
    if not data.get('name', '').strip():
        return jsonify({'error': 'Supplier name is required.'}), 400

    s = Supplier(
        name     = data['name'].strip(),
        contact  = data.get('contact', '').strip(),
        email    = data.get('email',   '').strip(),
        phone    = data.get('phone',   '').strip(),
        category = data.get('category','').strip(),
        city     = data.get('city',    '').strip()
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201


# ── PUT /api/suppliers/<id>  (Manager+) ──────────────
@suppliers_bp.route('/api/suppliers/<int:sid>', methods=['PUT'])
@token_required
@require_permission('suppliers_write')
def update_supplier(sid):
    s    = Supplier.query.get_or_404(sid)
    data = request.get_json()
    s.name     = data.get('name',     s.name).strip()
    s.contact  = data.get('contact',  s.contact)
    s.email    = data.get('email',    s.email)
    s.phone    = data.get('phone',    s.phone)
    s.category = data.get('category', s.category)
    s.city     = data.get('city',     s.city)
    db.session.commit()
    return jsonify(s.to_dict()), 200


# ── DELETE /api/suppliers/<id>  (Admin only) ──────────
@suppliers_bp.route('/api/suppliers/<int:sid>', methods=['DELETE'])
@token_required
@require_permission('suppliers_delete')
def delete_supplier(sid):
    s = Supplier.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'message': f'Supplier "{s.name}" removed.'}), 200
