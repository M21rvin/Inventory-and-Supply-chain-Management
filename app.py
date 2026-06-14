import os
from flask import Flask, jsonify
from flask_cors import CORS
from models import db

# Load .env file manually — avoids dotenv parse errors crashing startup
def load_env(filepath='.env'):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip blank lines and comments
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, _, value = line.partition('=')
            key   = key.strip()
            value = value.strip().strip('"').strip("'")
            # Don't override existing environment variables
            if key and key not in os.environ:
                os.environ[key] = value

load_env()


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # ── Database URL ───────────────────────────────────────────
    # Default: SQLite (works locally with zero setup)
    # For cloud: set DB_URL in .env to mysql+pymysql://... or postgresql://...
    db_url = os.environ.get('DB_URL', 'sqlite:///ims_dev.db')

    # Safety check — if URL is still the placeholder from .env.example, use SQLite
    placeholder_strings = ['YOUR_DATABASE_URL', 'user:password@host', 'localhost:3306/ims_db']
    if any(p in db_url for p in placeholder_strings):
        print('⚠️  DB_URL looks like a placeholder. Using SQLite instead.')
        db_url = 'sqlite:///ims_dev.db'

    app.config['SQLALCHEMY_DATABASE_URI']        = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY']                     = os.environ.get('JWT_SECRET', 'ims-secret-2026')
    app.config['MAX_CONTENT_LENGTH']             = 16 * 1024 * 1024  # 16 MB upload limit

    # Only add pool options for non-SQLite databases
    if not db_url.startswith('sqlite'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle':  300,
        }

    # ── CORS ──────────────────────────────────────────────────
    origins = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS(app, resources={r'/api/*': {'origins': origins}}, supports_credentials=True)

    # ── Database ──────────────────────────────────────────────
    db.init_app(app)

    # ── Blueprints ────────────────────────────────────────────
    from routes.auth      import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.products  import products_bp
    from routes.orders    import orders_bp
    from routes.suppliers import suppliers_bp
    from routes.reports   import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(reports_bp)

    # ── Health check ──────────────────────────────────────────
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok', 'db': db_url.split('://')[0]}), 200

    # ── Error handlers ────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Endpoint not found.'}), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({'error': 'File too large. Max 16MB.'}), 413

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error.', 'detail': str(e)}), 500

    return app


app = create_app()


# ── Seed sample data on first run ─────────────────────────────
def seed_data():
    from models import User, Product, Supplier, Order
    from werkzeug.security import generate_password_hash

    if User.query.first():
        return   # already seeded — skip

    print('🌱 Seeding database with sample data...')

    users = [
        User(name='Admin',          email='admin@ims.com',  password=generate_password_hash('admin123'),  role='Admin',           dept='Management'),
        User(name='Raj Manager',    email='raj@ims.com',    password=generate_password_hash('raj123'),    role='Manager',         dept='Procurement'),
        User(name='Priya Analyst',  email='priya@ims.com',  password=generate_password_hash('priya123'),  role='Analyst',         dept='Analytics'),
        User(name='Arjun Staff',    email='arjun@ims.com',  password=generate_password_hash('arjun123'),  role='Warehouse Staff', dept='Warehouse'),
        User(name='Meera Employee', email='meera@ims.com',  password=generate_password_hash('meera123'),  role='Employee',        dept='Sales'),
    ]
    products = [
        Product(name='Wireless Headset Pro',  sku='WHP-001', category='Audio',       price=3499, quantity=84,  reorder_level=15, supplier='SoundWave Inc'),
        Product(name='USB-C Hub 7-Port',      sku='UCH-007', category='Accessories', price=1299, quantity=23,  reorder_level=10, supplier='TechLink Ltd'),
        Product(name='Mechanical Keyboard',   sku='MKB-104', category='Input',       price=4999, quantity=61,  reorder_level=20, supplier='KeyMaster Co'),
        Product(name='Laptop Stand Alloy',    sku='LSA-002', category='Accessories', price=899,  quantity=5,   reorder_level=10, supplier='ErgoDesk'),
        Product(name='4K Webcam 60fps',       sku='WCM-4K1', category='Video',       price=6499, quantity=47,  reorder_level=12, supplier='VisionTech'),
        Product(name='Noise Cancel Earbuds',  sku='NCE-210', category='Audio',       price=2199, quantity=3,   reorder_level=15, supplier='SoundWave Inc'),
        Product(name='HDMI 2.1 Cable 2m',    sku='HDM-021', category='Accessories', price=499,  quantity=120, reorder_level=30, supplier='CablePro'),
    ]
    suppliers = [
        Supplier(name='SoundWave Inc', contact='Raj Mehta',   email='raj@soundwave.com',   phone='+91 98765 43210', category='Audio',         city='Mumbai'),
        Supplier(name='TechLink Ltd',  contact='Priya Shah',  email='priya@techlink.in',   phone='+91 87654 32109', category='Accessories',   city='Pune'),
        Supplier(name='KeyMaster Co',  contact='Arjun Nair',  email='arjun@keymaster.com', phone='+91 76543 21098', category='Input Devices', city='Bangalore'),
        Supplier(name='ErgoDesk',      contact='Sneha Patel', email='sneha@ergodesk.in',   phone='+91 65432 10987', category='Accessories',   city='Ahmedabad'),
        Supplier(name='VisionTech',    contact='Karan Gupta', email='karan@visiontech.co', phone='+91 54321 09876', category='Video',         city='Delhi'),
        Supplier(name='CablePro',      contact='Meena Iyer',  email='meena@cablepro.com',  phone='+91 43210 98765', category='Cables',        city='Chennai'),
    ]
    orders = [
        Order(order_id='ORD-2241', product='Wireless Headset Pro', supplier='SoundWave Inc', qty=20, price=3499, status='Delivered',  order_date='2026-03-13'),
        Order(order_id='ORD-2240', product='USB-C Hub 7-Port',     supplier='TechLink Ltd',  qty=50, price=1299, status='Processing', order_date='2026-03-12'),
        Order(order_id='ORD-2239', product='Mechanical Keyboard',  supplier='KeyMaster Co',  qty=15, price=4999, status='Pending',    order_date='2026-03-11'),
        Order(order_id='ORD-2238', product='Laptop Stand Alloy',   supplier='ErgoDesk',      qty=30, price=899,  status='Delivered',  order_date='2026-03-10'),
        Order(order_id='ORD-2237', product='4K Webcam 60fps',      supplier='VisionTech',    qty=10, price=6499, status='Cancelled',  order_date='2026-03-09'),
        Order(order_id='ORD-2236', product='HDMI 2.1 Cable 2m',   supplier='CablePro',      qty=100,price=499,  status='Delivered',  order_date='2026-03-08'),
        Order(order_id='ORD-2235', product='Wireless Headset Pro', supplier='SoundWave Inc', qty=12, price=3499, status='Delivered',  order_date='2026-02-25'),
        Order(order_id='ORD-2234', product='Noise Cancel Earbuds', supplier='SoundWave Inc', qty=25, price=2199, status='Delivered',  order_date='2026-02-18'),
        Order(order_id='ORD-2233', product='4K Webcam 60fps',      supplier='VisionTech',    qty=8,  price=6499, status='Delivered',  order_date='2026-02-10'),
    ]

    db.session.add_all(users + products + suppliers + orders)
    db.session.commit()
    print('✅ Done. 5 users, 7 products, 6 suppliers, 9 orders seeded.')
    print('')
    print('👤 Test accounts:')
    print('   admin@ims.com   / admin123   (Admin - full access)')
    print('   raj@ims.com     / raj123     (Manager)')
    print('   priya@ims.com   / priya123   (Analyst - read reports)')
    print('   arjun@ims.com   / arjun123   (Warehouse Staff)')
    print('   meera@ims.com   / meera123   (Employee - limited)')


# ── Entry point ───────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()

    db_type = os.environ.get('DB_URL', 'sqlite').split('://')[0]
    print(f'')
    print(f'🚀 IMS running at http://127.0.0.1:5000')
    print(f'📦 Database: {db_type}')
    print(f'🌐 Open http://127.0.0.1:5000/login in your browser')
    print(f'')

    app.run(
        debug = os.environ.get('FLASK_DEBUG', 'True') == 'True',
        port  = 5000,
        host  = '127.0.0.1'
    )
