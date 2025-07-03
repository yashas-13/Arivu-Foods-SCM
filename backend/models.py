"""SQLAlchemy models mapping to database tables."""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Numeric
from datetime import datetime

# WHY: Provide ORM mappings for easier DB access; extend with more models later.
db = SQLAlchemy()


class PricingTier(db.Model):
    __tablename__ = 'pricing_tiers'
    
    tier_id = db.Column(db.Integer, primary_key=True)
    tier_name = db.Column(db.String(100), unique=True, nullable=False)
    min_discount_percentage = db.Column(Numeric(5, 2), nullable=False)
    max_discount_percentage = db.Column(Numeric(5, 2), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    retailers = db.relationship('Retailer', backref='pricing_tier', lazy=True)
    
    __table_args__ = (
        CheckConstraint('min_discount_percentage >= 0 AND min_discount_percentage <= 100'),
        CheckConstraint('max_discount_percentage >= 0 AND max_discount_percentage <= 100'),
    )


class Product(db.Model):
    __tablename__ = 'products'

    product_id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    upc_ean = db.Column(db.String(20), unique=True)
    product_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    brand = db.Column(db.String(100))
    mrp = db.Column(Numeric(10, 2), nullable=False)
    weight_per_unit = db.Column(Numeric(10, 3))
    unit_of_measure = db.Column(db.String(20))
    shelf_life_days = db.Column(db.Integer)
    storage_requirements = db.Column(db.String(255))
    is_perishable = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    batches = db.relationship('Batch', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    
    __table_args__ = (
        CheckConstraint('mrp >= 0'),
        CheckConstraint('weight_per_unit >= 0'),
        CheckConstraint('shelf_life_days >= 0'),
    )


class Batch(db.Model):
    __tablename__ = 'batches'
    
    batch_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    manufacturer_batch_number = db.Column(db.String(100), nullable=False)
    production_date = db.Column(db.Date, nullable=False)
    expiration_date = db.Column(db.Date, nullable=False)
    initial_quantity = db.Column(Numeric(10, 2), nullable=False)
    current_quantity = db.Column(Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    manufacturing_location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory_records = db.relationship('Inventory', backref='batch', lazy=True)
    order_items = db.relationship('OrderItem', backref='batch', lazy=True)
    quality_checks = db.relationship('QualityCheck', backref='batch', lazy=True)
    
    __table_args__ = (
        CheckConstraint('initial_quantity >= 0'),
        CheckConstraint('current_quantity >= 0'),
        CheckConstraint("status IN ('Received','In Stock','Dispatched','Expired','Recalled')"),
    )


class Retailer(db.Model):
    __tablename__ = 'retailers'
    
    retailer_id = db.Column(db.Integer, primary_key=True)
    retailer_name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    phone_number = db.Column(db.String(50))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    pricing_tier_id = db.Column(db.Integer, db.ForeignKey('pricing_tiers.tier_id'))
    account_status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='retailer', lazy=True)
    
    __table_args__ = (
        CheckConstraint("account_status IN ('Active','Inactive','On Hold')"),
    )


class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    inventory_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.batch_id'), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    quantity_on_hand = db.Column(Numeric(10, 2), nullable=False)
    reorder_point = db.Column(Numeric(10, 2))
    last_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('quantity_on_hand >= 0'),
        CheckConstraint('reorder_point >= 0'),
    )


class Order(db.Model):
    __tablename__ = 'orders'
    
    order_id = db.Column(db.Integer, primary_key=True)
    retailer_id = db.Column(db.Integer, db.ForeignKey('retailers.retailer_id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(Numeric(12, 2), nullable=False)
    order_status = db.Column(db.String(50), nullable=False)
    delivery_address = db.Column(db.Text, nullable=False)
    expected_delivery_date = db.Column(db.Date)
    discount_applied_overall = db.Column(Numeric(5, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    shipments = db.relationship('Shipment', backref='order', lazy=True)
    
    __table_args__ = (
        CheckConstraint('total_amount >= 0'),
        CheckConstraint("order_status IN ('Pending','Processing','Fulfilled','Shipped','Delivered','Cancelled')"),
    )


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.batch_id'))
    quantity = db.Column(Numeric(10, 2), nullable=False)
    unit_price = db.Column(Numeric(10, 2), nullable=False)
    line_total = db.Column(Numeric(12, 2), nullable=False)
    discount_percentage = db.Column(Numeric(5, 2), default=0.00)
    actual_sales_price = db.Column(Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('quantity > 0'),
        CheckConstraint('unit_price >= 0'),
        CheckConstraint('line_total >= 0'),
    )


class Shipment(db.Model):
    __tablename__ = 'shipments'
    
    shipment_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    carrier_name = db.Column(db.String(100))
    tracking_number = db.Column(db.String(100), unique=True)
    dispatch_date = db.Column(db.DateTime, nullable=False)
    delivery_date = db.Column(db.DateTime)
    shipment_status = db.Column(db.String(50), nullable=False)
    estimated_cost = db.Column(Numeric(10, 2))
    actual_cost = db.Column(Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("shipment_status IN ('Pending','In Transit','Delivered','Failed')"),
    )


class User(db.Model):
    __tablename__ = 'users'
    
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
    quality_checks = db.relationship('QualityCheck', backref='checker', lazy=True)
    resolved_alerts = db.relationship('Alert', backref='resolver', lazy=True)
    
    __table_args__ = (
        CheckConstraint("role IN ('Admin','Sales','Warehouse','Logistics','Quality Control')"),
    )


class QualityCheck(db.Model):
    __tablename__ = 'quality_checks'
    
    check_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.batch_id'), nullable=False)
    check_date = db.Column(db.DateTime, nullable=False)
    checked_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    result = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    issue_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("result IN ('Pass','Fail','Conditional')"),
    )


class Alert(db.Model):
    __tablename__ = 'alerts'
    
    alert_id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    target_table = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    threshold_value = db.Column(Numeric(10, 2))
    alert_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    resolved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("alert_type IN ('Expiration','Low Stock','Recall','Quality Issue')"),
        CheckConstraint("status IN ('New','Acknowledged','Resolved')"),
    )

# HOW: Add additional fields based on schemadb when expanding features.

