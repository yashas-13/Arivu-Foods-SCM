from flask import Blueprint, jsonify, request
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func
from .models import (
    db, Product, Batch, Retailer, PricingTier, Inventory, Order, OrderItem,
    Shipment, User, QualityCheck, Alert
)
from decimal import Decimal
import json

# Blueprint for API routes
bp = Blueprint('api', __name__, url_prefix='/api')


# Helper function to serialize objects
def serialize_object(obj):
    """Convert SQLAlchemy object to dictionary"""
    if obj is None:
        return None
    result = {}
    for key in obj.__table__.columns.keys():
        value = getattr(obj, key)
        if isinstance(value, (datetime, date)):
            result[key] = value.isoformat()
        elif isinstance(value, Decimal):
            result[key] = float(value)
        else:
            result[key] = value
    return result


# Health check endpoint
@bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint.
    WHY: Establish baseline API for monitoring availability.
    WHAT: closes initial setup ticket.
    HOW: Extend by adding authentication; roll back by removing blueprint registration.
    """
    return jsonify({'status': 'ok'})


# Dashboard Analytics
@bp.route('/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """Get comprehensive dashboard analytics"""
    try:
        # Basic counts
        total_products = Product.query.count()
        total_batches = Batch.query.count()
        total_retailers = Retailer.query.count()
        active_orders = Order.query.filter_by(order_status='Pending').count()
        
        # Inventory summary
        total_inventory = db.session.query(func.sum(Inventory.quantity_on_hand)).scalar() or 0
        
        # Near expiry batches (next 7 days)
        near_expiry = Batch.query.filter(
            Batch.expiration_date <= date.today() + timedelta(days=7),
            Batch.status == 'In Stock'
        ).count()
        
        # Low stock alerts
        low_stock = Inventory.query.filter(
            Inventory.quantity_on_hand <= Inventory.reorder_point
        ).count()
        
        # Recent orders (last 30 days)
        recent_orders = Order.query.filter(
            Order.order_date >= datetime.now() - timedelta(days=30)
        ).count()
        
        # Total sales (last 30 days)
        total_sales = db.session.query(func.sum(Order.total_amount)).filter(
            Order.order_date >= datetime.now() - timedelta(days=30)
        ).scalar() or 0
        
        return jsonify({
            'total_products': total_products,
            'total_batches': total_batches,
            'total_retailers': total_retailers,
            'active_orders': active_orders,
            'total_inventory': float(total_inventory),
            'near_expiry_batches': near_expiry,
            'low_stock_alerts': low_stock,
            'recent_orders': recent_orders,
            'total_sales': float(total_sales)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Product Management
@bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        products = Product.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'products': [serialize_object(p) for p in products.items],
            'total': products.total,
            'pages': products.pages,
            'current_page': products.page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/products', methods=['POST'])
def create_product():
    """Create a new product"""
    try:
        data = request.get_json()
        
        product = Product(
            sku=data['sku'],
            product_name=data['product_name'],
            description=data.get('description'),
            category=data.get('category'),
            brand=data.get('brand'),
            mrp=Decimal(str(data['mrp'])),
            weight_per_unit=Decimal(str(data.get('weight_per_unit', 0))),
            unit_of_measure=data.get('unit_of_measure'),
            shelf_life_days=data.get('shelf_life_days'),
            storage_requirements=data.get('storage_requirements'),
            is_perishable=data.get('is_perishable', True)
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify(serialize_object(product)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Batch Management with FIFO/FEFO
@bp.route('/batches', methods=['GET'])
def get_batches():
    """Get all batches with FIFO/FEFO ordering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        query = db.session.query(Batch, Product).select_from(Batch).join(
            Product, Batch.product_id == Product.product_id
        )
        
        if status:
            query = query.filter(Batch.status == status)
        
        # Order by expiration date (FEFO) then production date (FIFO)
        query = query.order_by(Batch.expiration_date.asc(), Batch.production_date.asc())
        
        # Manual pagination
        total = query.count()
        batches_data = query.offset((page - 1) * per_page).limit(per_page).all()
        
        batch_list = []
        for batch, product in batches_data:
            batch_dict = serialize_object(batch)
            batch_dict['product_name'] = product.product_name
            batch_list.append(batch_dict)
        
        return jsonify({
            'batches': batch_list,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/batches', methods=['POST'])
def create_batch():
    """Create a new batch"""
    try:
        data = request.get_json()
        
        batch = Batch(
            product_id=data['product_id'],
            manufacturer_batch_number=data['manufacturer_batch_number'],
            production_date=datetime.strptime(data['production_date'], '%Y-%m-%d').date(),
            expiration_date=datetime.strptime(data['expiration_date'], '%Y-%m-%d').date(),
            initial_quantity=Decimal(str(data['initial_quantity'])),
            current_quantity=Decimal(str(data['initial_quantity'])),
            status='In Stock',  # Changed from 'Received' to 'In Stock'
            manufacturing_location=data.get('manufacturing_location')
        )
        
        db.session.add(batch)
        db.session.commit()
        
        # Create inventory record
        inventory = Inventory(
            batch_id=batch.batch_id,
            location=data.get('location', 'Main Warehouse'),
            quantity_on_hand=batch.initial_quantity,
            reorder_point=Decimal(str(data.get('reorder_point', 0)))
        )
        
        db.session.add(inventory)
        db.session.commit()
        
        return jsonify(serialize_object(batch)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/batches/<int:batch_id>/status', methods=['PUT'])
def update_batch_status(batch_id):
    """Update batch status for testing"""
    try:
        data = request.get_json()
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({'error': 'Batch not found'}), 404
        
        batch.status = data['status']
        db.session.commit()
        
        return jsonify(serialize_object(batch))
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Retailer Management
@bp.route('/retailers', methods=['GET'])
def get_retailers():
    """Get all retailers"""
    try:
        retailers = Retailer.query.all()
        return jsonify([serialize_object(r) for r in retailers])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/retailers', methods=['POST'])
def create_retailer():
    """Create a new retailer"""
    try:
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
        
        return jsonify(serialize_object(retailer)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Pricing Tiers
@bp.route('/pricing-tiers', methods=['GET'])
def get_pricing_tiers():
    """Get all pricing tiers"""
    try:
        tiers = PricingTier.query.all()
        return jsonify([serialize_object(t) for t in tiers])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/pricing-tiers', methods=['POST'])
def create_pricing_tier():
    """Create a new pricing tier"""
    try:
        data = request.get_json()
        
        tier = PricingTier(
            tier_name=data['tier_name'],
            min_discount_percentage=Decimal(str(data['min_discount_percentage'])),
            max_discount_percentage=Decimal(str(data['max_discount_percentage'])),
            description=data.get('description'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(tier)
        db.session.commit()
        
        return jsonify(serialize_object(tier)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Dynamic Pricing
@bp.route('/pricing/calculate', methods=['POST'])
def calculate_dynamic_pricing():
    """Calculate dynamic pricing for a retailer"""
    try:
        data = request.get_json()
        retailer_id = data['retailer_id']
        product_id = data['product_id']
        quantity = Decimal(str(data['quantity']))
        
        # Get retailer and product
        retailer = Retailer.query.get(retailer_id)
        product = Product.query.get(product_id)
        
        if not retailer or not product:
            return jsonify({'error': 'Retailer or product not found'}), 404
        
        # Base price is MRP
        base_price = product.mrp
        
        # Get pricing tier discount
        discount_percentage = Decimal('0')
        if retailer.pricing_tier:
            # Use average of min and max for simplicity
            discount_percentage = (
                retailer.pricing_tier.min_discount_percentage +
                retailer.pricing_tier.max_discount_percentage
            ) / 2
        
        # Volume-based discount (simple example)
        if quantity >= 100:
            discount_percentage += Decimal('5')  # Additional 5% for large orders
        
        # Calculate final price
        discount_amount = base_price * (discount_percentage / 100)
        final_price = base_price - discount_amount
        
        return jsonify({
            'base_price': float(base_price),
            'discount_percentage': float(discount_percentage),
            'discount_amount': float(discount_amount),
            'final_price': float(final_price),
            'total_amount': float(final_price * quantity)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Order Management
@bp.route('/orders', methods=['GET'])
def get_orders():
    """Get all orders"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Query orders with retailer information
        query = db.session.query(Order, Retailer).select_from(Order).join(
            Retailer, Order.retailer_id == Retailer.retailer_id
        ).order_by(Order.order_date.desc())
        
        # Manual pagination
        total = query.count()
        orders_data = query.offset((page - 1) * per_page).limit(per_page).all()
        
        order_list = []
        for order, retailer in orders_data:
            order_dict = serialize_object(order)
            order_dict['retailer_name'] = retailer.retailer_name
            order_list.append(order_dict)
        
        return jsonify({
            'orders': order_list,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/orders', methods=['POST'])
def create_order():
    """Create a new order with FIFO/FEFO allocation"""
    try:
        data = request.get_json()
        
        # Create order
        order = Order(
            retailer_id=data['retailer_id'],
            order_date=datetime.now(),
            total_amount=Decimal('0'),  # Will be calculated
            order_status='Pending',
            delivery_address=data['delivery_address'],
            expected_delivery_date=datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date()
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        total_amount = Decimal('0')
        
        # Process order items
        for item_data in data['items']:
            product_id = item_data['product_id']
            quantity_needed = Decimal(str(item_data['quantity']))
            
            # Find available batches using FIFO/FEFO
            available_batches = Batch.query.filter(
                Batch.product_id == product_id,
                Batch.status == 'In Stock',
                Batch.current_quantity > 0
            ).order_by(Batch.expiration_date.asc(), Batch.production_date.asc()).all()
            
            remaining_quantity = quantity_needed
            
            for batch in available_batches:
                if remaining_quantity <= 0:
                    break
                
                # Calculate how much to take from this batch
                take_quantity = min(remaining_quantity, batch.current_quantity)
                
                # Calculate pricing
                retailer = Retailer.query.get(data['retailer_id'])
                product = Product.query.get(product_id)
                
                # Simple pricing calculation
                base_price = product.mrp
                discount_percentage = Decimal('20')  # Default 20% discount
                
                if retailer.pricing_tier:
                    discount_percentage = (
                        retailer.pricing_tier.min_discount_percentage +
                        retailer.pricing_tier.max_discount_percentage
                    ) / 2
                
                unit_price = base_price * (1 - discount_percentage / 100)
                line_total = unit_price * take_quantity
                
                # Create order item
                order_item = OrderItem(
                    order_id=order.order_id,
                    product_id=product_id,
                    batch_id=batch.batch_id,
                    quantity=take_quantity,
                    unit_price=base_price,
                    line_total=line_total,
                    discount_percentage=discount_percentage,
                    actual_sales_price=unit_price
                )
                
                db.session.add(order_item)
                
                # Update batch quantity
                batch.current_quantity -= take_quantity
                remaining_quantity -= take_quantity
                total_amount += line_total
                
                # Update inventory quantity
                inventory_record = Inventory.query.filter_by(batch_id=batch.batch_id).first()
                if inventory_record:
                    inventory_record.quantity_on_hand -= take_quantity
            
            if remaining_quantity > 0:
                db.session.rollback()
                return jsonify({'error': f'Insufficient inventory for product {product_id}'}), 400
        
        # Update order total
        order.total_amount = total_amount
        db.session.commit()
        
        return jsonify(serialize_object(order)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Inventory Management
@bp.route('/inventory', methods=['GET'])
def get_inventory():
    """Get inventory with FIFO/FEFO ordering"""
    try:
        # Join with batch and product for comprehensive view
        inventory_query = db.session.query(
            Inventory, Batch, Product
        ).select_from(Inventory).join(
            Batch, Inventory.batch_id == Batch.batch_id
        ).join(
            Product, Batch.product_id == Product.product_id
        ).order_by(
            Batch.expiration_date.asc(), Batch.production_date.asc()
        )
        
        inventory_data = []
        for inv, batch, product in inventory_query:
            item = {
                'inventory_id': inv.inventory_id,
                'batch_id': batch.batch_id,
                'product_name': product.product_name,
                'sku': product.sku,
                'batch_number': batch.manufacturer_batch_number,
                'production_date': batch.production_date.isoformat(),
                'expiration_date': batch.expiration_date.isoformat(),
                'quantity_on_hand': float(inv.quantity_on_hand),
                'reorder_point': float(inv.reorder_point or 0),
                'location': inv.location,
                'status': batch.status,
                'days_to_expiry': (batch.expiration_date - date.today()).days
            }
            inventory_data.append(item)
        
        return jsonify(inventory_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Alerts
@bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts"""
    try:
        alerts = Alert.query.filter_by(status='New').order_by(Alert.alert_date.desc()).all()
        return jsonify([serialize_object(a) for a in alerts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/alerts/check', methods=['POST'])
def check_alerts():
    """Check for expiration and low stock alerts"""
    try:
        alerts_created = []
        
        # Check for expiring batches (next 7 days)
        expiring_batches = Batch.query.filter(
            Batch.expiration_date <= date.today() + timedelta(days=7),
            Batch.status == 'In Stock',
            Batch.current_quantity > 0
        ).all()
        
        for batch in expiring_batches:
            # Check if alert already exists
            existing_alert = Alert.query.filter_by(
                alert_type='Expiration',
                target_id=batch.batch_id,
                target_table='batches',
                status='New'
            ).first()
            
            if not existing_alert:
                days_to_expiry = (batch.expiration_date - date.today()).days
                alert = Alert(
                    alert_type='Expiration',
                    target_id=batch.batch_id,
                    target_table='batches',
                    message=f'Batch {batch.manufacturer_batch_number} expires in {days_to_expiry} days',
                    status='New'
                )
                db.session.add(alert)
                alerts_created.append(alert)
        
        # Check for low stock
        low_stock_inventory = Inventory.query.filter(
            Inventory.quantity_on_hand <= Inventory.reorder_point
        ).all()
        
        for inv in low_stock_inventory:
            existing_alert = Alert.query.filter_by(
                alert_type='Low Stock',
                target_id=inv.inventory_id,
                target_table='inventory',
                status='New'
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    alert_type='Low Stock',
                    target_id=inv.inventory_id,
                    target_table='inventory',
                    message=f'Low stock alert: {inv.location} - Quantity: {inv.quantity_on_hand}',
                    threshold_value=inv.reorder_point,
                    status='New'
                )
                db.session.add(alert)
                alerts_created.append(alert)
        
        db.session.commit()
        
        return jsonify({
            'alerts_created': len(alerts_created),
            'alerts': [serialize_object(a) for a in alerts_created]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Sales Analytics
@bp.route('/analytics/sales', methods=['GET'])
def get_sales_analytics():
    """Get comprehensive sales analytics"""
    try:
        # Date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Sales by product
        sales_by_product = db.session.query(
            Product.product_name,
            Product.sku,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.line_total).label('total_sales'),
            func.count(OrderItem.order_item_id).label('order_count')
        ).select_from(OrderItem).join(
            Product, OrderItem.product_id == Product.product_id
        ).join(
            Order, OrderItem.order_id == Order.order_id
        ).filter(
            Order.order_date >= start_date,
            Order.order_date <= end_date
        ).group_by(Product.product_id, Product.product_name, Product.sku).all()
        
        # Sales by retailer
        sales_by_retailer = db.session.query(
            Retailer.retailer_name,
            func.sum(Order.total_amount).label('total_sales'),
            func.count(Order.order_id).label('order_count')
        ).select_from(Order).join(
            Retailer, Order.retailer_id == Retailer.retailer_id
        ).filter(
            Order.order_date >= start_date,
            Order.order_date <= end_date
        ).group_by(Retailer.retailer_id, Retailer.retailer_name).all()
        
        # Sales by batch (traceability)
        sales_by_batch = db.session.query(
            Batch.manufacturer_batch_number,
            Product.product_name,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.line_total).label('total_sales')
        ).select_from(OrderItem).join(
            Batch, OrderItem.batch_id == Batch.batch_id
        ).join(
            Product, Batch.product_id == Product.product_id
        ).join(
            Order, OrderItem.order_id == Order.order_id
        ).filter(
            Order.order_date >= start_date,
            Order.order_date <= end_date
        ).group_by(Batch.batch_id, Batch.manufacturer_batch_number, Product.product_name).all()
        
        return jsonify({
            'date_range': {'start': start_date, 'end': end_date},
            'sales_by_product': [
                {
                    'product_name': row.product_name,
                    'sku': row.sku,
                    'total_quantity': float(row.total_quantity or 0),
                    'total_sales': float(row.total_sales or 0),
                    'order_count': row.order_count
                } for row in sales_by_product
            ],
            'sales_by_retailer': [
                {
                    'retailer_name': row.retailer_name,
                    'total_sales': float(row.total_sales or 0),
                    'order_count': row.order_count
                } for row in sales_by_retailer
            ],
            'sales_by_batch': [
                {
                    'batch_number': row.manufacturer_batch_number,
                    'product_name': row.product_name,
                    'total_quantity': float(row.total_quantity or 0),
                    'total_sales': float(row.total_sales or 0)
                } for row in sales_by_batch
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Data seeding for testing
@bp.route('/seed-data', methods=['POST'])
def seed_data():
    """Seed database with sample data for testing"""
    try:
        # Create pricing tiers
        tier1 = PricingTier(
            tier_name='Strategic Partners',
            min_discount_percentage=Decimal('25'),
            max_discount_percentage=Decimal('30'),
            description='High volume, long-term contracts'
        )
        
        tier2 = PricingTier(
            tier_name='Key Accounts',
            min_discount_percentage=Decimal('20'),
            max_discount_percentage=Decimal('25'),
            description='Medium-to-high volume, established relationship'
        )
        
        db.session.add_all([tier1, tier2])
        db.session.commit()
        
        # Create sample products
        products = [
            Product(
                sku='MANGO-001',
                product_name='Organic Mango Pulp',
                description='Fresh organic mango pulp',
                category='Fruit Pulp',
                brand='Arivu Foods',
                mrp=Decimal('150.00'),
                weight_per_unit=Decimal('1.0'),
                unit_of_measure='kg',
                shelf_life_days=30,
                storage_requirements='Refrigerated',
                is_perishable=True
            ),
            Product(
                sku='RICE-001',
                product_name='Basmati Rice Premium',
                description='Premium quality basmati rice',
                category='Grains',
                brand='Arivu Foods',
                mrp=Decimal('200.00'),
                weight_per_unit=Decimal('5.0'),
                unit_of_measure='kg',
                shelf_life_days=365,
                storage_requirements='Dry, cool place',
                is_perishable=False
            )
        ]
        
        db.session.add_all(products)
        db.session.commit()
        
        # Create sample retailers
        retailers = [
            Retailer(
                retailer_name='Metro Supermarket',
                contact_person='John Doe',
                email='john@metro.com',
                phone_number='+1234567890',
                address='123 Main St',
                city='Mumbai',
                state='Maharashtra',
                zip_code='400001',
                pricing_tier_id=tier1.tier_id,
                account_status='Active'
            ),
            Retailer(
                retailer_name='Local Grocery Store',
                contact_person='Jane Smith',
                email='jane@local.com',
                phone_number='+1234567891',
                address='456 Oak Ave',
                city='Delhi',
                state='Delhi',
                zip_code='110001',
                pricing_tier_id=tier2.tier_id,
                account_status='Active'
            )
        ]
        
        db.session.add_all(retailers)
        db.session.commit()
        
        return jsonify({'message': 'Sample data created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

