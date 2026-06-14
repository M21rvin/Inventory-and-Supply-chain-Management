import jwt
import os
from functools import wraps
from flask import request, jsonify

# ── Role hierarchy — higher number = more access ──
ROLE_LEVELS = {
    'Admin':           5,
    'Manager':         4,
    'Analyst':         3,
    'Warehouse Staff': 2,
    'Employee':        1,
}

# ── Per-route permission matrix ──
# Format:  route_key: minimum role level required
PERMISSIONS = {
    # Dashboard — everyone
    'dashboard':         1,
    # Products — view: everyone | add/edit: Manager+ | delete: Admin only
    'products_read':     1,
    'products_write':    4,
    'products_delete':   5,
    # Suppliers — view: Analyst+ | full CRUD: Manager+
    'suppliers_read':    3,
    'suppliers_write':   4,
    'suppliers_delete':  5,
    # Orders — view: everyone | create: Employee+ | delete: Manager+
    'orders_read':       1,
    'orders_write':      1,
    'orders_delete':     4,
    # Reports — Analyst+
    'reports_read':      3,
    # Excel upload — Manager+
    'upload':            4,
    # User management — Admin only
    'users':             5,
}


def get_token():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth.split(' ')[1]
    return None


def decode_token(token):
    return jwt.decode(
        token,
        os.environ.get('JWT_SECRET', 'ims-secret-2026'),
        algorithms=['HS256']
    )


def token_required(f):
    """Verify JWT. Attaches request.current_user on success."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token()
        if not token:
            return jsonify({'error': 'Token missing. Please login.'}), 401
        try:
            payload = decode_token(token)
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Session expired. Please login again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token.'}), 401
        return f(*args, **kwargs)
    return decorated


def require_permission(permission_key):
    """
    Check role level against PERMISSIONS map.
    Stack UNDER @token_required.

    Usage:
        @bp.route('/api/products', methods=['DELETE'])
        @token_required
        @require_permission('products_delete')
        def delete_product(id): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(request, 'current_user', None)
            if not user:
                return jsonify({'error': 'Not authenticated.'}), 401
            role       = user.get('role', 'Employee')
            user_level = ROLE_LEVELS.get(role, 0)
            req_level  = PERMISSIONS.get(permission_key, 99)
            if user_level < req_level:
                return jsonify({
                    'error': f'Access denied. This action requires {_min_role(req_level)} role or higher.',
                    'your_role': role
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def _min_role(level):
    for role, lv in ROLE_LEVELS.items():
        if lv == level:
            return role
    return 'Admin'
