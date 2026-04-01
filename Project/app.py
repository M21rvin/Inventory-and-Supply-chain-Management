from flask import Flask, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ims.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'ims-secret-key-2026'

db = SQLAlchemy(app)


# ════════════════════════════════════════
#  MODELS  (each class = one table in DB)
# ════════════════════════════════════════

class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Product(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), nullable=False)
    sku      = db.Column(db.String(50),  unique=True, nullable=False)
    category = db.Column(db.String(50))
    price    = db.Column(db.Float,  default=0)
    stock    = db.Column(db.Integer, default=0)
    supplier = db.Column(db.String(100))

class Supplier(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), nullable=False)
    contact  = db.Column(db.String(100))
    email    = db.Column(db.String(120))
    phone    = db.Column(db.String(20))
    category = db.Column(db.String(100))
    city     = db.Column(db.String(50))

class Order(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True, nullable=False)
    product  = db.Column(db.String(100), nullable=False)
    supplier = db.Column(db.String(100))
    qty      = db.Column(db.Integer, default=1)
    price    = db.Column(db.Float,   default=0)
    date     = db.Column(db.String(20))
    status   = db.Column(db.String(20), default='Pending')


# ════════════════════════════════════════
#  HELPER — turn a model row into a dict
# ════════════════════════════════════════

def product_dict(p):
    return {
        'id': p.id, 'name': p.name, 'sku': p.sku,
        'category': p.category, 'price': p.price,
        'stock': p.stock, 'supplier': p.supplier
    }

def supplier_dict(s):
    return {
        'id': s.id, 'name': s.name, 'contact': s.contact,
        'email': s.email, 'phone': s.phone,
        'category': s.category, 'city': s.city
    }

def order_dict(o):
    return {
        'id': o.id, 'order_id': o.order_id, 'product': o.product,
        'supplier': o.supplier, 'qty': o.qty, 'price': o.price,
        'date': o.date, 'status': o.status
    }


# ════════════════════════════════════════
#  AUTH ROUTES
# ════════════════════════════════════════

# POST /api/register  — create a new user
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    hashed = generate_password_hash(data['password'])
    user = User(name=data['name'], email=data['email'], password=hashed)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Registered successfully'}), 201


# POST /api/login  — login with email + password
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    session['user_id'] = user.id
    return jsonify({'message': 'Login successful', 'name': user.name}), 200


# POST /api/logout
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200


# ════════════════════════════════════════
#  PRODUCT ROUTES
# ════════════════════════════════════════

# GET  /api/products       — get all products
# POST /api/products       — add a new product
@app.route('/api/products', methods=['GET', 'POST'])
def products():
    if request.method == 'GET':
        all_products = Product.query.all()
        return jsonify([product_dict(p) for p in all_products])

    if request.method == 'POST':
        data = request.json
        # Check if SKU already exists
        if Product.query.filter_by(sku=data['sku']).first():
            return jsonify({'error': 'SKU already exists'}), 400
        p = Product(
            name=data['name'],     sku=data['sku'],
            category=data.get('category', ''),
            price=data.get('price', 0),
            stock=data.get('stock', 0),
            supplier=data.get('supplier', '')
        )
        db.session.add(p)
        db.session.commit()
        return jsonify(product_dict(p)), 201


# GET    /api/products/<id>  — get one product
# PUT    /api/products/<id>  — edit a product
# DELETE /api/products/<id>  — delete a product
@app.route('/api/products/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def product_detail(id):
    p = Product.query.get_or_404(id)

    if request.method == 'GET':
        return jsonify(product_dict(p))

    if request.method == 'PUT':
        data = request.json
        p.name     = data.get('name',     p.name)
        p.sku      = data.get('sku',      p.sku)
        p.category = data.get('category', p.category)
        p.price    = data.get('price',    p.price)
        p.stock    = data.get('stock',    p.stock)
        p.supplier = data.get('supplier', p.supplier)
        db.session.commit()
        return jsonify(product_dict(p))

    if request.method == 'DELETE':
        db.session.delete(p)
        db.session.commit()
        return jsonify({'message': 'Product deleted'})


# ════════════════════════════════════════
#  SUPPLIER ROUTES
# ════════════════════════════════════════

@app.route('/api/suppliers', methods=['GET', 'POST'])
def suppliers():
    if request.method == 'GET':
        all_suppliers = Supplier.query.all()
        return jsonify([supplier_dict(s) for s in all_suppliers])

    if request.method == 'POST':
        data = request.json
        s = Supplier(
            name=data['name'],
            contact=data.get('contact', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            category=data.get('category', ''),
            city=data.get('city', '')
        )
        db.session.add(s)
        db.session.commit()
        return jsonify(supplier_dict(s)), 201


@app.route('/api/suppliers/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def supplier_detail(id):
    s = Supplier.query.get_or_404(id)

    if request.method == 'GET':
        return jsonify(supplier_dict(s))

    if request.method == 'PUT':
        data = request.json
        s.name     = data.get('name',     s.name)
        s.contact  = data.get('contact',  s.contact)
        s.email    = data.get('email',    s.email)
        s.phone    = data.get('phone',    s.phone)
        s.category = data.get('category', s.category)
        s.city     = data.get('city',     s.city)
        db.session.commit()
        return jsonify(supplier_dict(s))

    if request.method == 'DELETE':
        db.session.delete(s)
        db.session.commit()
        return jsonify({'message': 'Supplier deleted'})


# ════════════════════════════════════════
#  ORDER ROUTES
# ════════════════════════════════════════

@app.route('/api/orders', methods=['GET', 'POST'])
def orders():
    if request.method == 'GET':
        all_orders = Order.query.order_by(Order.id.desc()).all()
        return jsonify([order_dict(o) for o in all_orders])

    if request.method == 'POST':
        data = request.json
        # Auto-generate order ID like ORD-2242
        last = Order.query.order_by(Order.id.desc()).first()
        num  = int(last.order_id.split('-')[1]) + 1 if last else 2241
        o = Order(
            order_id=f'ORD-{num}',
            product=data['product'],
            supplier=data.get('supplier', ''),
            qty=data.get('qty', 1),
            price=data.get('price', 0),
            date=data.get('date', datetime.today().strftime('%Y-%m-%d')),
            status=data.get('status', 'Pending')
        )
        db.session.add(o)
        db.session.commit()
        return jsonify(order_dict(o)), 201


@app.route('/api/orders/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def order_detail(id):
    o = Order.query.get_or_404(id)

    if request.method == 'GET':
        return jsonify(order_dict(o))

    if request.method == 'PUT':
        data = request.json
        o.product  = data.get('product',  o.product)
        o.supplier = data.get('supplier', o.supplier)
        o.qty      = data.get('qty',      o.qty)
        o.price    = data.get('price',    o.price)
        o.date     = data.get('date',     o.date)
        o.status   = data.get('status',   o.status)
        db.session.commit()
        return jsonify(order_dict(o))

    if request.method == 'DELETE':
        db.session.delete(o)
        db.session.commit()
        return jsonify({'message': 'Order deleted'})


# ════════════════════════════════════════
#  DASHBOARD STATS ROUTE
# ════════════════════════════════════════

@app.route('/api/stats', methods=['GET'])
def stats():
    total_products  = Product.query.count()
    total_suppliers = Supplier.query.count()
    total_orders    = Order.query.count()
    low_stock       = Product.query.filter(Product.stock <= 10).count()
    return jsonify({
        'total_products':  total_products,
        'total_suppliers': total_suppliers,
        'total_orders':    total_orders,
        'low_stock':       low_stock
    })


# ════════════════════════════════════════
#  SEED DATA  (run once to fill database)
# ════════════════════════════════════════

def seed_data():
    # Only seed if tables are empty
    if Product.query.first():
        return

    products = [
        Product(name='Wireless Headset Pro', sku='WHP-001', category='Audio',       price=3499, stock=84, supplier='SoundWave Inc'),
        Product(name='USB-C Hub 7-Port',     sku='UCH-007', category='Accessories', price=1299, stock=23, supplier='TechLink Ltd'),
        Product(name='Mechanical Keyboard',  sku='MKB-104', category='Input',       price=4999, stock=61, supplier='KeyMaster Co'),
        Product(name='Laptop Stand Alloy',   sku='LSA-002', category='Accessories', price=899,  stock=5,  supplier='ErgoDesk'),
        Product(name='4K Webcam 60fps',      sku='WCM-4K1', category='Video',       price=6499, stock=47, supplier='VisionTech'),
        Product(name='Noise Cancel Earbuds', sku='NCE-210', category='Audio',       price=2199, stock=3,  supplier='SoundWave Inc'),
        Product(name='HDMI 2.1 Cable 2m',   sku='HDM-021', category='Accessories', price=499,  stock=120,supplier='CablePro'),
    ]
    suppliers = [
        Supplier(name='SoundWave Inc', contact='Raj Mehta',   email='raj@soundwave.com',   phone='+91 98765 43210', category='Audio',            city='Mumbai'),
        Supplier(name='TechLink Ltd',  contact='Priya Shah',  email='priya@techlink.in',   phone='+91 87654 32109', category='Accessories',       city='Pune'),
        Supplier(name='KeyMaster Co',  contact='Arjun Nair',  email='arjun@keymaster.com', phone='+91 76543 21098', category='Input Devices',     city='Bangalore'),
        Supplier(name='ErgoDesk',      contact='Sneha Patel', email='sneha@ergodesk.in',   phone='+91 65432 10987', category='Accessories',       city='Ahmedabad'),
        Supplier(name='VisionTech',    contact='Karan Gupta', email='karan@visiontech.co', phone='+91 54321 09876', category='Video Equipment',   city='Delhi'),
        Supplier(name='CablePro',      contact='Meena Iyer',  email='meena@cablepro.com',  phone='+91 43210 98765', category='Cables',            city='Chennai'),
    ]
    orders = [
        Order(order_id='ORD-2241', product='Wireless Headset Pro', supplier='SoundWave Inc', qty=20, price=3499, date='2026-03-13', status='Delivered'),
        Order(order_id='ORD-2240', product='USB-C Hub 7-Port',     supplier='TechLink Ltd',  qty=50, price=1299, date='2026-03-12', status='Processing'),
        Order(order_id='ORD-2239', product='Mechanical Keyboard',  supplier='KeyMaster Co',  qty=15, price=4999, date='2026-03-11', status='Pending'),
        Order(order_id='ORD-2238', product='Laptop Stand Alloy',   supplier='ErgoDesk',      qty=30, price=899,  date='2026-03-10', status='Delivered'),
        Order(order_id='ORD-2237', product='4K Webcam 60fps',      supplier='VisionTech',    qty=10, price=6499, date='2026-03-09', status='Cancelled'),
        Order(order_id='ORD-2236', product='HDMI 2.1 Cable 2m',    supplier='CablePro',      qty=100,price=499,  date='2026-03-08', status='Delivered'),
    ]
    # Default admin user
    admin = User(
        name='Admin',
        email='admin@ims.com',
        password=generate_password_hash('admin123')
    )
    db.session.add_all(products + suppliers + orders + [admin])
    db.session.commit()
    print('✅ Database seeded with sample data')


# ════════════════════════════════════════
#  START THE SERVER
# ════════════════════════════════════════

if __name__ == '__main__':
    with app.app_context():
        db.create_all()   # create tables
        seed_data()       # fill with sample data
    app.run(debug=True)