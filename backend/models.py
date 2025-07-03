"""SQLAlchemy models mapping to database tables."""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from enum import Enum

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
    retailers = db.relationship('Retailer', backref='pricing_tier', lazy=True)


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
    batches = db.relationship('Batch', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)


class Batch(db.Model):
    __tablename__ = 'Batches'

    batch_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('Products.product_id'), nullable=False)
    manufacturer_batch_number = db.Column(db.String(100), nullable=False)
    production_date = db.Column(db.Date, nullable=False)
    expiration_date = db.Column(db.Date, nullable=False)
    initial_quantity = db.Column(db.Numeric(10, 2), nullable=False)
    current_quantity = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # 'Received','In Stock','Dispatched','Expired','Recalled'
    manufacturing_location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    inventory_records = db.relationship('Inventory', backref='batch', lazy=True)
    order_items = db.relationship('OrderItem', backref='batch', lazy=True)
    quality_checks = db.relationship('QualityCheck', backref='batch', lazy=True)


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
    account_status = db.Column(db.String(50), nullable=False)  # 'Active','Inactive','On Hold'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders = db.relationship('Order', backref='retailer', lazy=True)


class Inventory(db.Model):
    __tablename__ = 'Inventory'

    inventory_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('Batches.batch_id'), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    quantity_on_hand = db.Column(db.Numeric(10, 2), nullable=False)
    reorder_point = db.Column(db.Numeric(10, 2))
    last_updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    __tablename__ = 'Orders'

    order_id = db.Column(db.Integer, primary_key=True)
    retailer_id = db.Column(db.Integer, db.ForeignKey('Retailers.retailer_id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    order_status = db.Column(db.String(50), nullable=False)  # 'Pending','Processing','Fulfilled','Shipped','Delivered','Cancelled'
    delivery_address = db.Column(db.Text, nullable=False)
    expected_delivery_date = db.Column(db.Date)
    discount_applied_overall = db.Column(db.Numeric(5, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    shipments = db.relationship('Shipment', backref='order', lazy=True)


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


class Shipment(db.Model):
    __tablename__ = 'Shipments'

    shipment_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.order_id'), nullable=False)
    carrier_name = db.Column(db.String(100))
    tracking_number = db.Column(db.String(100), unique=True)
    dispatch_date = db.Column(db.DateTime, nullable=False)
    delivery_date = db.Column(db.DateTime)
    shipment_status = db.Column(db.String(50), nullable=False)  # 'Pending','In Transit','Delivered','Failed'
    estimated_cost = db.Column(db.Numeric(10, 2))
    actual_cost = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(db.Model):
    __tablename__ = 'Users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    role = db.Column(db.String(50), nullable=False)  # 'Admin','Sales','Warehouse','Logistics','Quality Control'
    is_active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    quality_checks = db.relationship('QualityCheck', backref='checked_by_user', lazy=True)
    resolved_alerts = db.relationship('Alert', backref='resolved_by_user', lazy=True)


class QualityCheck(db.Model):
    __tablename__ = 'QualityChecks'

    check_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('Batches.batch_id'), nullable=False)
    check_date = db.Column(db.DateTime, nullable=False)
    checked_by = db.Column(db.Integer, db.ForeignKey('Users.user_id'))
    result = db.Column(db.String(50), nullable=False)  # 'Pass','Fail','Conditional'
    notes = db.Column(db.Text)
    issue_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(db.Model):
    __tablename__ = 'Alerts'

    alert_id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)  # 'Expiration','Low Stock','Recall','Quality Issue'
    target_id = db.Column(db.Integer, nullable=False)
    target_table = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    threshold_value = db.Column(db.Numeric(10, 2))
    alert_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)  # 'New','Acknowledged','Resolved'
    resolved_by = db.Column(db.Integer, db.ForeignKey('Users.user_id'))
    resolved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

