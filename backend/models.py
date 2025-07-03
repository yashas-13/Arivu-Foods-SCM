"""SQLAlchemy models mapping to database tables."""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from decimal import Decimal

# WHY: Provide ORM mappings for easier DB access; extend with more models later.
db = SQLAlchemy()


class PricingTier(db.Model):
    __tablename__ = 'PricingTiers'

    tier_id = db.Column(db.Integer, primary_key=True)
    tier_name = db.Column(db.String(100), unique=True, nullable=False)
    min_discount_percentage = db.Column(db.Numeric(5, 2), nullable=False)
    max_discount_percentage = db.Column(db.Numeric(5, 2), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    retailers = db.relationship('Retailer', back_populates='pricing_tier')

    def to_dict(self):
        return {
            'tier_id': self.tier_id,
            'tier_name': self.tier_name,
            'min_discount_percentage': float(self.min_discount_percentage),
            'max_discount_percentage': float(self.max_discount_percentage),
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Product(db.Model):
    __tablename__ = 'Products'

    product_id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    upc_ean = db.Column(db.String(20), unique=True)
    product_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    brand = db.Column(db.String(100))
    mrp = db.Column(db.Numeric(10, 2), nullable=False)
    weight_per_unit = db.Column(db.Numeric(10, 3))
    unit_of_measure = db.Column(db.String(20))
    shelf_life_days = db.Column(db.Integer)
    storage_requirements = db.Column(db.String(255))
    is_perishable = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    batches = db.relationship('Batch', back_populates='product')
    order_items = db.relationship('OrderItem', back_populates='product')

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'sku': self.sku,
            'upc_ean': self.upc_ean,
            'product_name': self.product_name,
            'description': self.description,
            'category': self.category,
            'brand': self.brand,
            'mrp': float(self.mrp),
            'weight_per_unit': float(self.weight_per_unit) if self.weight_per_unit else None,
            'unit_of_measure': self.unit_of_measure,
            'shelf_life_days': self.shelf_life_days,
            'storage_requirements': self.storage_requirements,
            'is_perishable': self.is_perishable,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Batch(db.Model):
    __tablename__ = 'Batches'

    batch_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('Products.product_id'), nullable=False)
    manufacturer_batch_number = db.Column(db.String(100), nullable=False)
    production_date = db.Column(db.Date, nullable=False)
    expiration_date = db.Column(db.Date, nullable=False)
    initial_quantity = db.Column(db.Numeric(10, 2), nullable=False)
    current_quantity = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    manufacturing_location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', back_populates='batches')
    inventory = db.relationship('Inventory', back_populates='batch')
    order_items = db.relationship('OrderItem', back_populates='batch')
    quality_checks = db.relationship('QualityCheck', back_populates='batch')

    def to_dict(self):
        return {
            'batch_id': self.batch_id,
            'product_id': self.product_id,
            'manufacturer_batch_number': self.manufacturer_batch_number,
            'production_date': self.production_date.isoformat() if self.production_date else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'initial_quantity': float(self.initial_quantity),
            'current_quantity': float(self.current_quantity),
            'status': self.status,
            'manufacturing_location': self.manufacturing_location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Retailer(db.Model):
    __tablename__ = 'Retailers'

    retailer_id = db.Column(db.Integer, primary_key=True)
    retailer_name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    phone_number = db.Column(db.String(50))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    pricing_tier_id = db.Column(db.Integer, db.ForeignKey('PricingTiers.tier_id'))
    account_status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pricing_tier = db.relationship('PricingTier', back_populates='retailers')
    orders = db.relationship('Order', back_populates='retailer')

    def to_dict(self):
        return {
            'retailer_id': self.retailer_id,
            'retailer_name': self.retailer_name,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone_number': self.phone_number,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'pricing_tier_id': self.pricing_tier_id,
            'account_status': self.account_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Inventory(db.Model):
    __tablename__ = 'Inventory'

    inventory_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('Batches.batch_id'), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    quantity_on_hand = db.Column(db.Numeric(10, 2), nullable=False)
    reorder_point = db.Column(db.Numeric(10, 2))
    last_updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    batch = db.relationship('Batch', back_populates='inventory')

    def to_dict(self):
        return {
            'inventory_id': self.inventory_id,
            'batch_id': self.batch_id,
            'location': self.location,
            'quantity_on_hand': float(self.quantity_on_hand),
            'reorder_point': float(self.reorder_point) if self.reorder_point else None,
            'last_updated_at': self.last_updated_at.isoformat() if self.last_updated_at else None
        }


class Order(db.Model):
    __tablename__ = 'Orders'

    order_id = db.Column(db.Integer, primary_key=True)
    retailer_id = db.Column(db.Integer, db.ForeignKey('Retailers.retailer_id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    order_status = db.Column(db.String(50), nullable=False)
    delivery_address = db.Column(db.Text, nullable=False)
    expected_delivery_date = db.Column(db.Date)
    discount_applied_overall = db.Column(db.Numeric(5, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    retailer = db.relationship('Retailer', back_populates='orders')
    order_items = db.relationship('OrderItem', back_populates='order')
    shipments = db.relationship('Shipment', back_populates='order')

    def to_dict(self):
        return {
            'order_id': self.order_id,
            'retailer_id': self.retailer_id,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'total_amount': float(self.total_amount),
            'order_status': self.order_status,
            'delivery_address': self.delivery_address,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'discount_applied_overall': float(self.discount_applied_overall),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class OrderItem(db.Model):
    __tablename__ = 'OrderItems'

    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.order_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('Products.product_id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('Batches.batch_id'))
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0.00)
    actual_sales_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')
    batch = db.relationship('Batch', back_populates='order_items')

    def to_dict(self):
        return {
            'order_item_id': self.order_item_id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'batch_id': self.batch_id,
            'quantity': float(self.quantity),
            'unit_price': float(self.unit_price),
            'line_total': float(self.line_total),
            'discount_percentage': float(self.discount_percentage),
            'actual_sales_price': float(self.actual_sales_price),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Shipment(db.Model):
    __tablename__ = 'Shipments'

    shipment_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.order_id'), nullable=False)
    carrier_name = db.Column(db.String(100))
    tracking_number = db.Column(db.String(100), unique=True)
    dispatch_date = db.Column(db.DateTime, nullable=False)
    delivery_date = db.Column(db.DateTime)
    shipment_status = db.Column(db.String(50), nullable=False)
    estimated_cost = db.Column(db.Numeric(10, 2))
    actual_cost = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = db.relationship('Order', back_populates='shipments')

    def to_dict(self):
        return {
            'shipment_id': self.shipment_id,
            'order_id': self.order_id,
            'carrier_name': self.carrier_name,
            'tracking_number': self.tracking_number,
            'dispatch_date': self.dispatch_date.isoformat() if self.dispatch_date else None,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'shipment_status': self.shipment_status,
            'estimated_cost': float(self.estimated_cost) if self.estimated_cost else None,
            'actual_cost': float(self.actual_cost) if self.actual_cost else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class User(db.Model):
    __tablename__ = 'Users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    role = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    quality_checks = db.relationship('QualityCheck', back_populates='user')
    resolved_alerts = db.relationship('Alert', back_populates='resolved_by_user')

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_active': self.is_active,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class QualityCheck(db.Model):
    __tablename__ = 'QualityChecks'

    check_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('Batches.batch_id'), nullable=False)
    check_date = db.Column(db.DateTime, nullable=False)
    checked_by = db.Column(db.Integer, db.ForeignKey('Users.user_id'))
    result = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    issue_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    batch = db.relationship('Batch', back_populates='quality_checks')
    user = db.relationship('User', back_populates='quality_checks')

    def to_dict(self):
        return {
            'check_id': self.check_id,
            'batch_id': self.batch_id,
            'check_date': self.check_date.isoformat() if self.check_date else None,
            'checked_by': self.checked_by,
            'result': self.result,
            'notes': self.notes,
            'issue_description': self.issue_description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Alert(db.Model):
    __tablename__ = 'Alerts'

    alert_id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    target_table = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    threshold_value = db.Column(db.Numeric(10, 2))
    alert_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('Users.user_id'))
    resolved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resolved_by_user = db.relationship('User', back_populates='resolved_alerts')

    def to_dict(self):
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type,
            'target_id': self.target_id,
            'target_table': self.target_table,
            'message': self.message,
            'threshold_value': float(self.threshold_value) if self.threshold_value else None,
            'alert_date': self.alert_date.isoformat() if self.alert_date else None,
            'status': self.status,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

