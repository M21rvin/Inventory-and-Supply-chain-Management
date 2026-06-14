import jwt
import os
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from middleware import token_required

auth_bp = Blueprint('auth', __name__)


def _make_token(user):
    exp = datetime.now(timezone.utc) + timedelta(hours=int(os.environ.get('JWT_EXPIRY_HOURS', 24)))
    payload = {
        'id':    user.id,
        'name':  user.name,
        'email': user.email,
        'role':  user.role,
        'dept':  user.dept,
        'exp':   exp
    }
    return jwt.encode(payload, os.environ.get('JWT_SECRET', 'ims-secret-2026'), algorithm='HS256')


# ── Serve login page ──────────────────────────────────
@auth_bp.route('/')
@auth_bp.route('/login')
def login_page():
    return render_template('login.html')


# ── POST /login ───────────────────────────────────────
@auth_bp.route('/login', methods=['POST'])
def login():
    data  = request.get_json()
    email = data.get('email', '').strip().lower()
    pwd   = data.get('password', '')

    if not email or not pwd:
        return jsonify({'success': False, 'message': 'Email and password required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, pwd):
        return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401

    if not user.is_active:
        return jsonify({'success': False, 'message': 'Account deactivated. Contact admin.'}), 403

    token = _make_token(user)
    return jsonify({
        'success': True,
        'token':   token,
        'user':    user.to_dict()
    }), 200


# ── POST /register ────────────────────────────────────
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name    = data.get('name', '').strip()
    email   = data.get('email', '').strip().lower()
    pwd     = data.get('password', '')
    confirm = data.get('confirm', '')
    role    = data.get('role', 'Employee')
    dept    = data.get('dept', '').strip()

    # Validation
    if not name or not email or not pwd:
        return jsonify({'success': False, 'message': 'Name, email and password are required.'}), 400
    if len(pwd) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters.'}), 400
    if pwd != confirm:
        return jsonify({'success': False, 'message': 'Passwords do not match.'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered.'}), 409

    # New registrations default to Employee — only Admin can assign higher roles
    # (Admin can use /api/users/<id> to change roles after)
    safe_role = role if role in ('Manager', 'Employee', 'Analyst', 'Warehouse Staff') else 'Employee'

    user = User(
        name     = name,
        email    = email,
        password = generate_password_hash(pwd),
        role     = safe_role,
        dept     = dept
    )
    db.session.add(user)
    db.session.commit()

    token = _make_token(user)
    return jsonify({
        'success': True,
        'message': 'Account created successfully.',
        'token':   token,
        'user':    user.to_dict()
    }), 201


# ── GET /api/me ───────────────────────────────────────
@auth_bp.route('/api/me')
@token_required
def me():
    uid  = request.current_user.get('id')
    user = User.query.get(uid)
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    return jsonify({'user': user.to_dict()}), 200


# ── POST /logout ──────────────────────────────────────
@auth_bp.route('/logout', methods=['POST'])
def logout():
    # JWT is stateless — client deletes the token
    return jsonify({'success': True, 'message': 'Logged out.'}), 200


# ── GET /api/users  (Admin only) ──────────────────────
@auth_bp.route('/api/users')
@token_required
def list_users():
    from middleware import require_permission, ROLE_LEVELS
    role = request.current_user.get('role', 'Employee')
    if ROLE_LEVELS.get(role, 0) < 5:
        return jsonify({'error': 'Admin access required.'}), 403
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users]), 200


# ── PUT /api/users/<id>/role  (Admin only) ────────────
@auth_bp.route('/api/users/<int:uid>/role', methods=['PUT'])
@token_required
def change_role(uid):
    from middleware import ROLE_LEVELS
    if ROLE_LEVELS.get(request.current_user.get('role'), 0) < 5:
        return jsonify({'error': 'Admin access required.'}), 403
    data    = request.get_json()
    new_role = data.get('role')
    user    = User.query.get_or_404(uid)
    user.role = new_role
    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict()}), 200
