from flask import Blueprint, jsonify, request
from sqlalchemy import desc, asc
from datetime import datetime, date
from .models import db, Product, Batch, Retailer, PricingTier, Order, OrderItem, Inventory, Alert
from .services import InventoryService, PricingService, AlertService

# Blueprint for API routes
bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint.
    WHY: Establish baseline API for monitoring availability.
    WHAT: closes initial setup ticket.
    HOW: Extend by adding authentication; roll back by removing blueprint registration.
    """
    return jsonify({'status': 'ok'})


# Product Management
@bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with pagination and filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    query = Product.query
    if search:
        query = query.filter(Product.product_name.contains(search) | Product.sku.contains(search))
    
    products = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'products': [{
            'product_id': p.product_id,
            'sku': p.sku,
            'product_name': p.product_name,
            'category': p.category,
            'brand': p.brand,
            'mrp': float(p.mrp) if p.mrp else 0,
            'is_perishable': p.is_perishable,
            'shelf_life_days': p.shelf_life_days
        } for p in products.items],
        'total': products.total,
        'pages': products.pages,
        'current_page': products.page
    })


@bp.route('/products', methods=['POST'])
def create_product():
    """Create a new product."""
    data = request.get_json()
    
    product = Product(
        sku=data['sku'],
        product_name=data['product_name'],
        description=data.get('description'),
        category=data.get('category'),
        brand=data.get('brand'),
        mrp=data['mrp'],
        weight_per_unit=data.get('weight_per_unit'),
        unit_of_measure=data.get('unit_of_measure'),
        shelf_life_days=data.get('shelf_life_days'),
        storage_requirements=data.get('storage_requirements'),
        is_perishable=data.get('is_perishable', True)
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({'message': 'Product created successfully', 'product_id': product.product_id}), 201


# Batch Management with FIFO/FEFO
@bp.route('/batches', methods=['GET'])
def get_batches():
    """Get all batches with FIFO/FEFO ordering."""
    # Default to FEFO (First Expiry First Out) for perishable goods
    sort_by = request.args.get('sort', 'expiration_date')  # or 'production_date' for FIFO
    product_id = request.args.get('product_id', type=int)
    
    query = Batch.query
    if product_id:
        query = query.filter(Batch.product_id == product_id)
    
    if sort_by == 'expiration_date':
        query = query.order_by(asc(Batch.expiration_date))  # FEFO
    else:
        query = query.order_by(asc(Batch.production_date))  # FIFO
    
    batches = query.all()
    
    return jsonify({
        'batches': [batch.to_dict() for batch in batches],
        'sort_method': 'FEFO' if sort_by == 'expiration_date' else 'FIFO'
    })


@bp.route('/batches', methods=['POST'])
def create_batch():
    """Create a new batch."""
    data = request.get_json()
    
    batch = Batch(
        product_id=data['product_id'],
        manufacturer_batch_number=data['manufacturer_batch_number'],
        production_date=datetime.strptime(data['production_date'], '%Y-%m-%d').date(),
        expiration_date=datetime.strptime(data['expiration_date'], '%Y-%m-%d').date(),
        initial_quantity=data['initial_quantity'],
        current_quantity=data['initial_quantity'],
        status='Received',
        manufacturing_location=data.get('manufacturing_location')
    )
    
    db.session.add(batch)
    db.session.commit()
    
    # Create inventory record for the batch
    inventory = Inventory(
        batch_id=batch.batch_id,
        location=data.get('location', 'Main Warehouse'),
        quantity_on_hand=batch.initial_quantity,
        reorder_point=data.get('reorder_point', 0)
    )
    db.session.add(inventory)
    db.session.commit()
    
    return jsonify({'message': 'Batch created successfully', 'batch_id': batch.batch_id}), 201


@bp.route('/batches/allocate', methods=['POST'])
def allocate_batch():
    """Allocate quantity from a batch using FIFO/FEFO logic."""
    data = request.get_json()
    product_id = data['product_id']
    quantity_needed = data['quantity']
    
    # Use InventoryService to handle FIFO/FEFO allocation
    allocated_batches = InventoryService.allocate_inventory(product_id, quantity_needed)
    
    if not allocated_batches:
        return jsonify({'error': 'Insufficient inventory available'}), 400
    
    return jsonify({
        'message': 'Batch allocation successful',
        'allocated_batches': allocated_batches
    })


# Retailer Management
@bp.route('/retailers', methods=['GET'])
def get_retailers():
    """Get all retailers with their pricing tiers."""
    retailers = Retailer.query.join(PricingTier, Retailer.pricing_tier_id == PricingTier.tier_id, isouter=True).all()
    
    return jsonify({
        'retailers': [{
            'retailer_id': r.retailer_id,
            'retailer_name': r.retailer_name,
            'email': r.email,
            'phone_number': r.phone_number,
            'city': r.city,
            'account_status': r.account_status,
            'pricing_tier': r.pricing_tier.tier_name if r.pricing_tier else None,
            'discount_range': f"{r.pricing_tier.min_discount_percentage}%-{r.pricing_tier.max_discount_percentage}%" if r.pricing_tier else None
        } for r in retailers]
    })


@bp.route('/retailers', methods=['POST'])
def create_retailer():
    """Create a new retailer."""
    data = request.get_json()
    
    retailer = Retailer(
        retailer_name=data['retailer_name'],
        contact_person=data.get('contact_person'),
        email=data.get('email'),
        phone_number=data.get('phone_number'),
        address=data.get('address'),
        city=data.get('city'),
        state=data.get('state'),
        zip_code=data.get('zip_code'),
        pricing_tier_id=data.get('pricing_tier_id'),
        account_status=data.get('account_status', 'Active')
    )
    
    db.session.add(retailer)
    db.session.commit()
    
    return jsonify({'message': 'Retailer created successfully', 'retailer_id': retailer.retailer_id}), 201


# Dynamic Pricing
@bp.route('/pricing/calculate', methods=['POST'])
def calculate_pricing():
    """Calculate dynamic pricing for a retailer."""
    data = request.get_json()
    retailer_id = data['retailer_id']
    product_id = data['product_id']
    quantity = data['quantity']
    
    # Use PricingService to calculate dynamic pricing
    pricing_info = PricingService.calculate_price(retailer_id, product_id, quantity)
    
    return jsonify(pricing_info)


# Analytics and Reporting
@bp.route('/analytics/sales', methods=['GET'])
def get_sales_analytics():
    """Get sales analytics and KPIs."""
    # Basic sales analytics
    from sqlalchemy import func
    
    # Total sales
    total_sales = db.session.query(func.sum(Order.total_amount)).scalar() or 0
    
    # Sales by product
    product_sales = db.session.query(
        Product.product_name,
        func.sum(OrderItem.line_total).label('total_sales'),
        func.sum(OrderItem.quantity).label('total_quantity')
    ).join(OrderItem).group_by(Product.product_id).all()
    
    # Sales by retailer
    retailer_sales = db.session.query(
        Retailer.retailer_name,
        func.sum(Order.total_amount).label('total_sales'),
        func.count(Order.order_id).label('order_count')
    ).join(Order).group_by(Retailer.retailer_id).all()
    
    return jsonify({
        'total_sales': float(total_sales),
        'product_sales': [{
            'product_name': ps[0],
            'total_sales': float(ps[1]),
            'total_quantity': float(ps[2])
        } for ps in product_sales],
        'retailer_sales': [{
            'retailer_name': rs[0],
            'total_sales': float(rs[1]),
            'order_count': rs[2]
        } for rs in retailer_sales]
    })


@bp.route('/analytics/inventory', methods=['GET'])
def get_inventory_analytics():
    """Get inventory analytics and KPIs."""
    from sqlalchemy import func
    
    # Inventory turnover and stock levels
    inventory_stats = db.session.query(
        Product.product_name,
        func.sum(Inventory.quantity_on_hand).label('total_stock'),
        func.min(Batch.expiration_date).label('earliest_expiry')
    ).join(Batch).join(Inventory).join(Product).group_by(Product.product_id).all()
    
    # Low stock alerts
    low_stock = db.session.query(
        Product.product_name,
        Inventory.quantity_on_hand,
        Inventory.reorder_point
    ).join(Batch).join(Product).filter(
        Inventory.quantity_on_hand <= Inventory.reorder_point
    ).all()
    
    return jsonify({
        'inventory_stats': [{
            'product_name': inv[0],
            'total_stock': float(inv[1]),
            'earliest_expiry': inv[2].isoformat() if inv[2] else None
        } for inv in inventory_stats],
        'low_stock_items': [{
            'product_name': ls[0],
            'current_stock': float(ls[1]),
            'reorder_point': float(ls[2]) if ls[2] else 0
        } for ls in low_stock]
    })


# Automated Alerts
@bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all active alerts."""
    alerts = Alert.query.filter(Alert.status == 'New').order_by(desc(Alert.alert_date)).all()
    
    return jsonify({
        'alerts': [{
            'alert_id': a.alert_id,
            'alert_type': a.alert_type,
            'message': a.message,
            'alert_date': a.alert_date.isoformat(),
            'status': a.status
        } for a in alerts]
    })


@bp.route('/alerts/expiration', methods=['GET'])
def get_expiration_alerts():
    """Get expiration alerts for batches nearing expiry."""
    alerts = AlertService.check_expiration_alerts()
    return jsonify({'expiration_alerts': alerts})


@bp.route('/alerts/low-stock', methods=['GET'])
def get_low_stock_alerts():
    """Get low stock alerts."""
    alerts = AlertService.check_low_stock_alerts()
    return jsonify({'low_stock_alerts': alerts})


# Dashboard Data
@bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get comprehensive dashboard data."""
    from sqlalchemy import func
    
    # Key metrics
    total_products = Product.query.count()
    total_batches = Batch.query.count()
    total_retailers = Retailer.query.count()
    active_orders = Order.query.filter(Order.order_status.in_(['Pending', 'Processing'])).count()
    
    # Recent orders
    recent_orders = Order.query.order_by(desc(Order.order_date)).limit(5).all()
    
    # Expiring batches (next 7 days)
    from datetime import timedelta
    expiring_soon = Batch.query.filter(
        Batch.expiration_date <= date.today() + timedelta(days=7)
    ).order_by(asc(Batch.expiration_date)).limit(5).all()
    
    # Active alerts
    active_alerts = Alert.query.filter(Alert.status == 'New').count()
    
    return jsonify({
        'metrics': {
            'total_products': total_products,
            'total_batches': total_batches,
            'total_retailers': total_retailers,
            'active_orders': active_orders,
            'active_alerts': active_alerts
        },
        'recent_orders': [{
            'order_id': o.order_id,
            'retailer_name': o.retailer.retailer_name,
            'total_amount': float(o.total_amount),
            'order_date': o.order_date.isoformat(),
            'status': o.order_status
        } for o in recent_orders],
        'expiring_batches': [{
            'batch_id': b.batch_id,
            'product_name': b.product.product_name,
            'expiration_date': b.expiration_date.isoformat(),
            'current_quantity': float(b.current_quantity)
        } for b in expiring_soon]
    })


@bp.route('/dashboard/kpis', methods=['GET'])
def get_dashboard_kpis():
    """Get key performance indicators for dashboard."""
    from sqlalchemy import func
    
    # Sales KPIs
    total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0
    avg_order_value = db.session.query(func.avg(Order.total_amount)).scalar() or 0
    
    # Inventory KPIs
    total_inventory_value = db.session.query(
        func.sum(Inventory.quantity_on_hand * Product.mrp)
    ).join(Batch).join(Product).scalar() or 0
    
    # Calculate inventory turnover (simplified)
    inventory_turnover = 0  # Would need more complex calculation with time periods
    
    return jsonify({
        'sales_kpis': {
            'total_revenue': float(total_revenue),
            'average_order_value': float(avg_order_value),
            'orders_this_month': Order.query.filter(
                func.extract('month', Order.order_date) == datetime.now().month
            ).count()
        },
        'inventory_kpis': {
            'total_inventory_value': float(total_inventory_value),
            'inventory_turnover': inventory_turnover,
            'low_stock_items': Inventory.query.filter(
                Inventory.quantity_on_hand <= Inventory.reorder_point
            ).count()
        }
    })

