from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    role       = db.Column(db.String(50),  default='Employee')   # Admin | Manager | Analyst | Warehouse Staff | Employee
    dept       = db.Column(db.String(100), default='')
    is_active  = db.Column(db.Boolean,     default=True)
    created_at = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'email': self.email,
            'role': self.role, 'dept': self.dept, 'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }


class Product(db.Model):
    __tablename__ = 'products'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    sku           = db.Column(db.String(50),  unique=True, nullable=False)
    category      = db.Column(db.String(50),  default='')
    price         = db.Column(db.Float,       default=0.0)
    quantity      = db.Column(db.Integer,     default=0)
    reorder_level = db.Column(db.Integer,     default=10)
    supplier      = db.Column(db.String(100), default='')
    created_at    = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'sku': self.sku,
            'category': self.category, 'price': self.price,
            'quantity': self.quantity, 'reorder_level': self.reorder_level,
            'supplier': self.supplier,
            'status': 'Out' if self.quantity == 0 else ('Low' if self.quantity <= self.reorder_level else 'In Stock')
        }


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    contact    = db.Column(db.String(100), default='')
    email      = db.Column(db.String(120), default='')
    phone      = db.Column(db.String(30),  default='')
    category   = db.Column(db.String(100), default='')
    city       = db.Column(db.String(50),  default='')
    created_at = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'contact': self.contact,
            'email': self.email, 'phone': self.phone,
            'category': self.category, 'city': self.city
        }


class Order(db.Model):
    __tablename__ = 'orders'
    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.String(20),  unique=True, nullable=False)
    product    = db.Column(db.String(100), nullable=False)
    supplier   = db.Column(db.String(100), default='')
    customer   = db.Column(db.String(100), default='')
    qty        = db.Column(db.Integer,     default=1)
    price      = db.Column(db.Float,       default=0.0)
    status     = db.Column(db.String(20),  default='Pending')
    order_date = db.Column(db.String(20),  default='')
    created_at = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id, 'order_id': self.order_id,
            'product': self.product, 'supplier': self.supplier,
            'customer': self.customer, 'qty': self.qty, 'price': self.price,
            'total': round(self.qty * self.price, 2),
            'status': self.status, 'date': self.order_date
        }
