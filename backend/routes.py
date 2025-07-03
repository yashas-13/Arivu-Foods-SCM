from flask import Blueprint, jsonify, request
from .models import db, Product, Batch, Retailer, PricingTier, Inventory, Order, OrderItem, Alert, User
from datetime import datetime, date, timedelta
from sqlalchemy import func, desc, asc
from decimal import Decimal
import requests
import os

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


# Product Management APIs
@bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with optional filtering."""
    try:
        query = Product.query
        
        # Filter by category if provided
        category = request.args.get('category')
        if category:
            query = query.filter(Product.category == category)
            
        # Filter by brand if provided
        brand = request.args.get('brand')
        if brand:
            query = query.filter(Product.brand == brand)
            
        # Search by name if provided
        search = request.args.get('search')
        if search:
            query = query.filter(Product.product_name.ilike(f'%{search}%'))
            
        products = query.all()
        
        return jsonify([{
            'product_id': p.product_id,
            'sku': p.sku,
            'product_name': p.product_name,
            'category': p.category,
            'brand': p.brand,
            'mrp': float(p.mrp),
            'is_perishable': p.is_perishable,
            'shelf_life_days': p.shelf_life_days,
            'storage_requirements': p.storage_requirements
        } for p in products])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/products', methods=['POST'])
def create_product():
    """Create a new product."""
    try:
        data = request.get_json()
        
        product = Product(
            sku=data['sku'],
            product_name=data['product_name'],
            category=data.get('category'),
            brand=data.get('brand'),
            mrp=Decimal(str(data['mrp'])),
            weight_per_unit=Decimal(str(data.get('weight_per_unit', 0))),
            unit_of_measure=data.get('unit_of_measure'),
            shelf_life_days=data.get('shelf_life_days'),
            storage_requirements=data.get('storage_requirements'),
            is_perishable=data.get('is_perishable', True),
            description=data.get('description')
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'product_id': product.product_id,
            'message': 'Product created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Batch Management APIs
@bp.route('/batches', methods=['GET'])
def get_batches():
    """Get all batches with optional filtering and FIFO/FEFO ordering."""
    try:
        query = Batch.query.join(Product)
        
        # Filter by product if provided
        product_id = request.args.get('product_id')
        if product_id:
            query = query.filter(Batch.product_id == product_id)
            
        # Filter by status if provided
        status = request.args.get('status')
        if status:
            query = query.filter(Batch.status == status)
            
        # Order by expiration date (FEFO) or production date (FIFO)
        order_by = request.args.get('order_by', 'expiration_date')
        if order_by == 'expiration_date':
            query = query.order_by(asc(Batch.expiration_date))
        else:
            query = query.order_by(asc(Batch.production_date))
            
        batches = query.all()
        
        return jsonify([{
            'batch_id': b.batch_id,
            'product_id': b.product_id,
            'product_name': b.product.product_name,
            'manufacturer_batch_number': b.manufacturer_batch_number,
            'production_date': b.production_date.isoformat(),
            'expiration_date': b.expiration_date.isoformat(),
            'initial_quantity': float(b.initial_quantity),
            'current_quantity': float(b.current_quantity),
            'status': b.status,
            'days_until_expiry': (b.expiration_date - date.today()).days
        } for b in batches])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/batches', methods=['POST'])
def create_batch():
    """Create a new batch."""
    try:
        data = request.get_json()
        
        batch = Batch(
            product_id=data['product_id'],
            manufacturer_batch_number=data['manufacturer_batch_number'],
            production_date=datetime.strptime(data['production_date'], '%Y-%m-%d').date(),
            expiration_date=datetime.strptime(data['expiration_date'], '%Y-%m-%d').date(),
            initial_quantity=Decimal(str(data['initial_quantity'])),
            current_quantity=Decimal(str(data['initial_quantity'])),
            status=data.get('status', 'Received'),
            manufacturing_location=data.get('manufacturing_location')
        )
        
        db.session.add(batch)
        db.session.commit()
        
        return jsonify({
            'batch_id': batch.batch_id,
            'message': 'Batch created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Retailer Management APIs
@bp.route('/retailers', methods=['GET'])
def get_retailers():
    """Get all retailers with their pricing tiers."""
    try:
        retailers = Retailer.query.outerjoin(PricingTier).all()
        
        return jsonify([{
            'retailer_id': r.retailer_id,
            'retailer_name': r.retailer_name,
            'contact_person': r.contact_person,
            'email': r.email,
            'phone_number': r.phone_number,
            'city': r.city,
            'state': r.state,
            'account_status': r.account_status,
            'pricing_tier': {
                'tier_id': r.pricing_tier.tier_id if r.pricing_tier else None,
                'tier_name': r.pricing_tier.tier_name if r.pricing_tier else None,
                'min_discount_percentage': float(r.pricing_tier.min_discount_percentage) if r.pricing_tier else None,
                'max_discount_percentage': float(r.pricing_tier.max_discount_percentage) if r.pricing_tier else None,
            } if r.pricing_tier else None
        } for r in retailers])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/retailers', methods=['POST'])
def create_retailer():
    """Create a new retailer."""
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
        
        return jsonify({
            'retailer_id': retailer.retailer_id,
            'message': 'Retailer created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Dynamic Pricing APIs
@bp.route('/pricing-tiers', methods=['GET'])
def get_pricing_tiers():
    """Get all pricing tiers."""
    try:
        tiers = PricingTier.query.filter_by(is_active=True).all()
        
        return jsonify([{
            'tier_id': t.tier_id,
            'tier_name': t.tier_name,
            'min_discount_percentage': float(t.min_discount_percentage),
            'max_discount_percentage': float(t.max_discount_percentage),
            'description': t.description
        } for t in tiers])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/pricing/calculate', methods=['POST'])
def calculate_pricing():
    """Calculate price for a product based on retailer's pricing tier."""
    try:
        data = request.get_json()
        product_id = data['product_id']
        retailer_id = data['retailer_id']
        quantity = data.get('quantity', 1)
        
        # Get product and retailer info
        product = Product.query.get(product_id)
        retailer = Retailer.query.get(retailer_id)
        
        if not product or not retailer:
            return jsonify({'error': 'Product or retailer not found'}), 404
            
        # Base price is MRP
        base_price = product.mrp
        
        # Apply discount based on retailer's pricing tier
        discount_percentage = 0
        if retailer.pricing_tier:
            # For this example, use the middle of the discount range
            discount_percentage = (retailer.pricing_tier.min_discount_percentage + 
                                 retailer.pricing_tier.max_discount_percentage) / 2
        
        # Calculate final price
        discount_amount = base_price * (discount_percentage / 100)
        final_price = base_price - discount_amount
        
        return jsonify({
            'product_id': product_id,
            'retailer_id': retailer_id,
            'base_price': float(base_price),
            'discount_percentage': float(discount_percentage),
            'discount_amount': float(discount_amount),
            'final_price': float(final_price),
            'quantity': quantity,
            'total_amount': float(final_price * quantity)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Inventory Management APIs
@bp.route('/inventory', methods=['GET'])
def get_inventory():
    """Get current inventory levels with FIFO/FEFO ordering."""
    try:
        # Get inventory with batch and product details
        inventory = db.session.query(
            Inventory,
            Batch,
            Product
        ).join(
            Batch, Inventory.batch_id == Batch.batch_id
        ).join(
            Product, Batch.product_id == Product.product_id
        ).filter(
            Inventory.quantity_on_hand > 0
        ).order_by(
            asc(Batch.expiration_date)  # FEFO ordering
        ).all()
        
        return jsonify([{
            'inventory_id': inv.inventory_id,
            'batch_id': inv.batch_id,
            'product_id': batch.product_id,
            'product_name': product.product_name,
            'sku': product.sku,
            'batch_number': batch.manufacturer_batch_number,
            'location': inv.location,
            'quantity_on_hand': float(inv.quantity_on_hand),
            'reorder_point': float(inv.reorder_point) if inv.reorder_point else None,
            'expiration_date': batch.expiration_date.isoformat(),
            'days_until_expiry': (batch.expiration_date - date.today()).days,
            'is_low_stock': inv.reorder_point and inv.quantity_on_hand <= inv.reorder_point
        } for inv, batch, product in inventory])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Analytics APIs
@bp.route('/analytics/sales-summary', methods=['GET'])
def get_sales_summary():
    """Get sales analytics and summary."""
    try:
        # Get date range parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Base query for order items
        query = db.session.query(
            OrderItem,
            Order,
            Product,
            Batch,
            Retailer
        ).join(
            Order, OrderItem.order_id == Order.order_id
        ).join(
            Product, OrderItem.product_id == Product.product_id
        ).outerjoin(
            Batch, OrderItem.batch_id == Batch.batch_id
        ).join(
            Retailer, Order.retailer_id == Retailer.retailer_id
        )
        
        # Apply date filters
        if start_date:
            query = query.filter(Order.order_date >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Order.order_date <= datetime.strptime(end_date, '%Y-%m-%d'))
            
        order_items = query.all()
        
        # Calculate analytics
        total_sales = sum(float(item.line_total) for item, _, _, _, _ in order_items)
        total_orders = len(set(item.order_id for item, _, _, _, _ in order_items))
        
        # Product sales breakdown
        product_sales = {}
        for item, order, product, batch, retailer in order_items:
            if product.product_id not in product_sales:
                product_sales[product.product_id] = {
                    'product_name': product.product_name,
                    'total_quantity': 0,
                    'total_revenue': 0
                }
            product_sales[product.product_id]['total_quantity'] += float(item.quantity)
            product_sales[product.product_id]['total_revenue'] += float(item.line_total)
        
        return jsonify({
            'total_sales': total_sales,
            'total_orders': total_orders,
            'product_sales': list(product_sales.values())
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Alert Management APIs
@bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all active alerts."""
    try:
        alerts = Alert.query.filter_by(status='New').order_by(desc(Alert.alert_date)).all()
        
        return jsonify([{
            'alert_id': a.alert_id,
            'alert_type': a.alert_type,
            'message': a.message,
            'alert_date': a.alert_date.isoformat(),
            'target_id': a.target_id,
            'target_table': a.target_table,
            'threshold_value': float(a.threshold_value) if a.threshold_value else None
        } for a in alerts])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/alerts/check-expiration', methods=['POST'])
def check_expiration_alerts():
    """Check for expiration alerts and create them."""
    try:
        # Get batches expiring in the next 7 days
        alert_threshold = date.today() + timedelta(days=7)
        expiring_batches = Batch.query.filter(
            Batch.expiration_date <= alert_threshold,
            Batch.status == 'In Stock'
        ).all()
        
        alerts_created = 0
        for batch in expiring_batches:
            # Check if alert already exists
            existing_alert = Alert.query.filter_by(
                alert_type='Expiration',
                target_id=batch.batch_id,
                target_table='Batches',
                status='New'
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    alert_type='Expiration',
                    target_id=batch.batch_id,
                    target_table='Batches',
                    message=f'Batch {batch.manufacturer_batch_number} of {batch.product.product_name} expires on {batch.expiration_date}',
                    status='New'
                )
                db.session.add(alert)
                alerts_created += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'{alerts_created} expiration alerts created',
            'alerts_created': alerts_created
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Weather Dashboard API
@bp.route('/weather', methods=['GET'])
def get_weather():
    """Get current weather data for supply chain locations."""
    try:
        # Default location (you can make this configurable)
        city = request.args.get('city', 'New York')
        
        # Using OpenWeatherMap API (you'll need to set API key in environment)
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return jsonify({
                'error': 'Weather API key not configured',
                'mock_data': {
                    'city': city,
                    'temperature': 22.5,
                    'humidity': 65,
                    'description': 'Clear sky',
                    'wind_speed': 5.2
                }
            })
        
        # Make API call to OpenWeatherMap
        url = f'https://api.openweathermap.org/data/2.5/weather'
        params = {
            'q': city,
            'appid': api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'city': data['name'],
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'wind_speed': data['wind']['speed'],
                'pressure': data['main']['pressure']
            })
        else:
            return jsonify({'error': 'Weather API request failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Order Management APIs
@bp.route('/orders', methods=['GET'])
def get_orders():
    """Get all orders with optional filtering."""
    try:
        query = Order.query.join(Retailer)
        
        # Filter by retailer if provided
        retailer_id = request.args.get('retailer_id')
        if retailer_id:
            query = query.filter(Order.retailer_id == retailer_id)
            
        # Filter by status if provided
        status = request.args.get('status')
        if status:
            query = query.filter(Order.order_status == status)
            
        # Filter by date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if start_date:
            query = query.filter(Order.order_date >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Order.order_date <= datetime.strptime(end_date, '%Y-%m-%d'))
            
        orders = query.order_by(desc(Order.order_date)).all()
        
        return jsonify([{
            'order_id': o.order_id,
            'retailer_name': o.retailer.retailer_name,
            'order_date': o.order_date.isoformat(),
            'total_amount': float(o.total_amount),
            'order_status': o.order_status,
            'expected_delivery_date': o.expected_delivery_date.isoformat() if o.expected_delivery_date else None,
            'discount_applied_overall': float(o.discount_applied_overall)
        } for o in orders])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/orders', methods=['POST'])
def create_order():
    """Create a new order with line items."""
    try:
        data = request.get_json()
        
        # Create order
        order = Order(
            retailer_id=data['retailer_id'],
            order_date=datetime.utcnow(),
            total_amount=Decimal('0.00'),  # Will be calculated
            order_status='Pending',
            delivery_address=data['delivery_address'],
            expected_delivery_date=datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date() if data.get('expected_delivery_date') else None
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        total_amount = Decimal('0.00')
        
        # Create order items
        for item_data in data['items']:
            # Get pricing for this retailer
            pricing_response = calculate_pricing_internal(
                item_data['product_id'],
                data['retailer_id'],
                item_data['quantity']
            )
            
            # Allocate batch (FIFO/FEFO)
            batch = allocate_batch_quantity(
                item_data['product_id'],
                item_data['quantity']
            )
            
            if not batch:
                raise ValueError(f"Insufficient stock for product {item_data['product_id']}")
            
            order_item = OrderItem(
                order_id=order.order_id,
                product_id=item_data['product_id'],
                batch_id=batch.batch_id,
                quantity=Decimal(str(item_data['quantity'])),
                unit_price=Decimal(str(pricing_response['base_price'])),
                discount_percentage=Decimal(str(pricing_response['discount_percentage'])),
                actual_sales_price=Decimal(str(pricing_response['final_price'])),
                line_total=Decimal(str(pricing_response['total_amount']))
            )
            
            db.session.add(order_item)
            total_amount += order_item.line_total
        
        # Update order total
        order.total_amount = total_amount
        
        db.session.commit()
        
        return jsonify({
            'order_id': order.order_id,
            'total_amount': float(total_amount),
            'message': 'Order created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def calculate_pricing_internal(product_id, retailer_id, quantity):
    """Internal function to calculate pricing."""
    product = Product.query.get(product_id)
    retailer = Retailer.query.get(retailer_id)
    
    if not product or not retailer:
        raise ValueError('Product or retailer not found')
        
    base_price = product.mrp
    discount_percentage = 0
    
    if retailer.pricing_tier:
        discount_percentage = (retailer.pricing_tier.min_discount_percentage + 
                             retailer.pricing_tier.max_discount_percentage) / 2
    
    discount_amount = base_price * (discount_percentage / 100)
    final_price = base_price - discount_amount
    
    return {
        'base_price': float(base_price),
        'discount_percentage': float(discount_percentage),
        'discount_amount': float(discount_amount),
        'final_price': float(final_price),
        'total_amount': float(final_price * quantity)
    }


def allocate_batch_quantity(product_id, required_quantity):
    """Allocate quantity from available batches using FIFO/FEFO."""
    # Get available batches ordered by expiration date (FEFO)
    batches = Batch.query.filter(
        Batch.product_id == product_id,
        Batch.status == 'In Stock',
        Batch.current_quantity > 0
    ).order_by(asc(Batch.expiration_date)).all()
    
    remaining_quantity = Decimal(str(required_quantity))
    
    for batch in batches:
        if remaining_quantity <= 0:
            break
            
        if batch.current_quantity >= remaining_quantity:
            # This batch has enough quantity
            batch.current_quantity -= remaining_quantity
            remaining_quantity = 0
            return batch
        else:
            # Take all from this batch and continue
            remaining_quantity -= batch.current_quantity
            batch.current_quantity = 0
            batch.status = 'Dispatched'
    
    if remaining_quantity > 0:
        # Insufficient stock
        return None
    
    return batches[0]  # Return the first batch used


# Dashboard Summary API
@bp.route('/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """Get summary data for the main dashboard."""
    try:
        # Get current counts
        total_products = Product.query.count()
        total_batches = Batch.query.count()
        active_retailers = Retailer.query.filter_by(account_status='Active').count()
        pending_orders = Order.query.filter_by(order_status='Pending').count()
        
        # Get recent alerts
        recent_alerts = Alert.query.filter_by(status='New').order_by(desc(Alert.alert_date)).limit(5).all()
        
        # Get low stock items
        low_stock_items = db.session.query(
            Inventory,
            Product,
            Batch
        ).join(
            Batch, Inventory.batch_id == Batch.batch_id
        ).join(
            Product, Batch.product_id == Product.product_id
        ).filter(
            Inventory.reorder_point.isnot(None),
            Inventory.quantity_on_hand <= Inventory.reorder_point
        ).limit(10).all()
        
        # Get expiring batches
        expiring_soon = Batch.query.filter(
            Batch.expiration_date <= date.today() + timedelta(days=7),
            Batch.status == 'In Stock'
        ).order_by(asc(Batch.expiration_date)).limit(10).all()
        
        return jsonify({
            'counts': {
                'total_products': total_products,
                'total_batches': total_batches,
                'active_retailers': active_retailers,
                'pending_orders': pending_orders
            },
            'recent_alerts': [{
                'alert_id': a.alert_id,
                'alert_type': a.alert_type,
                'message': a.message,
                'alert_date': a.alert_date.isoformat()
            } for a in recent_alerts],
            'low_stock_items': [{
                'product_name': product.product_name,
                'batch_number': batch.manufacturer_batch_number,
                'current_quantity': float(inventory.quantity_on_hand),
                'reorder_point': float(inventory.reorder_point),
                'location': inventory.location
            } for inventory, product, batch in low_stock_items],
            'expiring_soon': [{
                'batch_id': b.batch_id,
                'product_name': b.product.product_name,
                'batch_number': b.manufacturer_batch_number,
                'expiration_date': b.expiration_date.isoformat(),
                'days_until_expiry': (b.expiration_date - date.today()).days,
                'current_quantity': float(b.current_quantity)
            } for b in expiring_soon]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

