from flask import Blueprint, jsonify, request
from .models import db, Product, Batch, Retailer, Order, OrderItem, Inventory, PricingTier, Alert, Shipment, User, QualityCheck
from datetime import datetime, date
from decimal import Decimal
import traceback

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


# Product Management Endpoints
@bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with optional filtering."""
    try:
        category = request.args.get('category')
        is_perishable = request.args.get('is_perishable')
        
        query = Product.query
        if category:
            query = query.filter(Product.category == category)
        if is_perishable is not None:
            query = query.filter(Product.is_perishable == (is_perishable.lower() == 'true'))
        
        products = query.all()
        return jsonify([product.to_dict() for product in products])
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
            description=data.get('description'),
            category=data.get('category'),
            brand=data.get('brand'),
            mrp=Decimal(str(data['mrp'])),
            weight_per_unit=Decimal(str(data['weight_per_unit'])) if data.get('weight_per_unit') else None,
            unit_of_measure=data.get('unit_of_measure'),
            shelf_life_days=data.get('shelf_life_days'),
            storage_requirements=data.get('storage_requirements'),
            is_perishable=data.get('is_perishable', True),
            upc_ean=data.get('upc_ean')
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify(product.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID."""
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify(product.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 404


@bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product."""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        # Update fields if provided
        for field in ['sku', 'product_name', 'description', 'category', 'brand', 
                     'unit_of_measure', 'shelf_life_days', 'storage_requirements', 
                     'is_perishable', 'upc_ean']:
            if field in data:
                setattr(product, field, data[field])
        
        # Handle decimal fields
        if 'mrp' in data:
            product.mrp = Decimal(str(data['mrp']))
        if 'weight_per_unit' in data:
            product.weight_per_unit = Decimal(str(data['weight_per_unit'])) if data['weight_per_unit'] else None
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(product.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# Batch Management Endpoints
@bp.route('/batches', methods=['GET'])
def get_batches():
    """Get all batches with optional filtering."""
    try:
        product_id = request.args.get('product_id')
        status = request.args.get('status')
        expiring_soon = request.args.get('expiring_soon')  # days
        
        query = Batch.query
        if product_id:
            query = query.filter(Batch.product_id == product_id)
        if status:
            query = query.filter(Batch.status == status)
        if expiring_soon:
            days = int(expiring_soon)
            cutoff_date = datetime.now().date()
            from datetime import timedelta
            cutoff_date += timedelta(days=days)
            query = query.filter(Batch.expiration_date <= cutoff_date)
        
        # Order by expiration date (FIFO/FEFO)
        batches = query.order_by(Batch.expiration_date.asc()).all()
        return jsonify([batch.to_dict() for batch in batches])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/batches', methods=['POST'])
def create_batch():
    """Create a new batch."""
    try:
        data = request.get_json()
        
        # Convert date strings to date objects
        production_date = datetime.strptime(data['production_date'], '%Y-%m-%d').date()
        expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date()
        
        batch = Batch(
            product_id=data['product_id'],
            manufacturer_batch_number=data['manufacturer_batch_number'],
            production_date=production_date,
            expiration_date=expiration_date,
            initial_quantity=Decimal(str(data['initial_quantity'])),
            current_quantity=Decimal(str(data['current_quantity'])),
            status=data.get('status', 'Received'),
            manufacturing_location=data.get('manufacturing_location')
        )
        
        db.session.add(batch)
        db.session.commit()
        
        return jsonify(batch.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@bp.route('/batches/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    """Get a specific batch by ID."""
    try:
        batch = Batch.query.get_or_404(batch_id)
        return jsonify(batch.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 404


@bp.route('/batches/<int:batch_id>', methods=['PUT'])
def update_batch(batch_id):
    """Update a batch."""
    try:
        batch = Batch.query.get_or_404(batch_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'current_quantity' in data:
            batch.current_quantity = Decimal(str(data['current_quantity']))
        if 'status' in data:
            batch.status = data['status']
        if 'manufacturing_location' in data:
            batch.manufacturing_location = data['manufacturing_location']
        
        batch.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(batch.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# Retailer Management Endpoints
@bp.route('/retailers', methods=['GET'])
def get_retailers():
    """Get all retailers."""
    try:
        retailers = Retailer.query.all()
        return jsonify([retailer.to_dict() for retailer in retailers])
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
        
        return jsonify(retailer.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@bp.route('/retailers/<int:retailer_id>', methods=['GET'])
def get_retailer(retailer_id):
    """Get a specific retailer by ID."""
    try:
        retailer = Retailer.query.get_or_404(retailer_id)
        return jsonify(retailer.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 404


# Pricing Tier Management
@bp.route('/pricing-tiers', methods=['GET'])
def get_pricing_tiers():
    """Get all pricing tiers."""
    try:
        tiers = PricingTier.query.filter_by(is_active=True).all()
        return jsonify([tier.to_dict() for tier in tiers])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/pricing-tiers', methods=['POST'])
def create_pricing_tier():
    """Create a new pricing tier."""
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
        
        return jsonify(tier.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# Dynamic Pricing Endpoint
@bp.route('/pricing/calculate', methods=['POST'])
def calculate_pricing():
    """Calculate dynamic pricing for a product based on retailer tier."""
    try:
        data = request.get_json()
        product_id = data['product_id']
        retailer_id = data['retailer_id']
        quantity = Decimal(str(data.get('quantity', 1)))
        
        # Get product and retailer info
        product = Product.query.get_or_404(product_id)
        retailer = Retailer.query.get_or_404(retailer_id)
        
        if not retailer.pricing_tier:
            return jsonify({'error': 'Retailer has no pricing tier assigned'}), 400
        
        # Calculate base discount from tier
        tier = retailer.pricing_tier
        base_discount = tier.max_discount_percentage  # Use max by default
        
        # Volume-based discount (example: 5% additional for orders > 100 units)
        volume_discount = Decimal('0')
        if quantity > 100:
            volume_discount = Decimal('5')
        
        # Total discount (capped at tier max)
        total_discount = min(base_discount + volume_discount, tier.max_discount_percentage)
        
        # Calculate final price
        discount_amount = (product.mrp * total_discount) / 100
        final_price = product.mrp - discount_amount
        
        return jsonify({
            'product_id': product_id,
            'retailer_id': retailer_id,
            'mrp': float(product.mrp),
            'base_discount_percentage': float(base_discount),
            'volume_discount_percentage': float(volume_discount),
            'total_discount_percentage': float(total_discount),
            'discount_amount': float(discount_amount),
            'final_price': float(final_price),
            'quantity': float(quantity),
            'line_total': float(final_price * quantity)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Order Management Endpoints
@bp.route('/orders', methods=['GET'])
def get_orders():
    """Get all orders with optional filtering."""
    try:
        retailer_id = request.args.get('retailer_id')
        status = request.args.get('status')
        
        query = Order.query
        if retailer_id:
            query = query.filter(Order.retailer_id == retailer_id)
        if status:
            query = query.filter(Order.order_status == status)
        
        orders = query.order_by(Order.order_date.desc()).all()
        return jsonify([order.to_dict() for order in orders])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/orders', methods=['POST'])
def create_order():
    """Create a new order with FIFO/FEFO batch allocation."""
    try:
        data = request.get_json()
        
        # Create order
        order = Order(
            retailer_id=data['retailer_id'],
            order_date=datetime.utcnow(),
            total_amount=Decimal('0'),  # Will be calculated
            order_status='Pending',
            delivery_address=data['delivery_address'],
            expected_delivery_date=datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date() if data.get('expected_delivery_date') else None
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        total_amount = Decimal('0')
        
        # Process order items with FIFO/FEFO allocation
        for item_data in data['order_items']:
            product_id = item_data['product_id']
            requested_quantity = Decimal(str(item_data['quantity']))
            
            # Get available batches for this product (FIFO/FEFO order)
            available_batches = Batch.query.filter(
                Batch.product_id == product_id,
                Batch.status == 'In Stock',
                Batch.current_quantity > 0
            ).order_by(Batch.expiration_date.asc()).all()
            
            if not available_batches:
                db.session.rollback()
                return jsonify({'error': f'No available batches for product {product_id}'}), 400
            
            # Calculate pricing for this retailer
            retailer = Retailer.query.get_or_404(data['retailer_id'])
            product = Product.query.get_or_404(product_id)
            
            # Get pricing tier discount
            discount_percentage = Decimal('0')
            if retailer.pricing_tier:
                discount_percentage = retailer.pricing_tier.max_discount_percentage
            
            unit_price = product.mrp * (1 - discount_percentage / 100)
            
            # Allocate from batches using FIFO/FEFO
            remaining_quantity = requested_quantity
            
            for batch in available_batches:
                if remaining_quantity <= 0:
                    break
                
                # Allocate from this batch
                allocated_quantity = min(remaining_quantity, batch.current_quantity)
                
                # Create order item
                order_item = OrderItem(
                    order_id=order.order_id,
                    product_id=product_id,
                    batch_id=batch.batch_id,
                    quantity=allocated_quantity,
                    unit_price=unit_price,
                    line_total=unit_price * allocated_quantity,
                    discount_percentage=discount_percentage,
                    actual_sales_price=unit_price
                )
                
                db.session.add(order_item)
                
                # Update batch quantity
                batch.current_quantity -= allocated_quantity
                batch.updated_at = datetime.utcnow()
                
                # Update total amount
                total_amount += order_item.line_total
                
                remaining_quantity -= allocated_quantity
            
            if remaining_quantity > 0:
                db.session.rollback()
                return jsonify({'error': f'Insufficient stock for product {product_id}. Available: {requested_quantity - remaining_quantity}, Requested: {requested_quantity}'}), 400
        
        # Update order total
        order.total_amount = total_amount
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(order.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get a specific order with items."""
    try:
        order = Order.query.get_or_404(order_id)
        order_dict = order.to_dict()
        
        # Add order items
        order_dict['order_items'] = [item.to_dict() for item in order.order_items]
        
        return jsonify(order_dict)
    except Exception as e:
        return jsonify({'error': str(e)}), 404


# Inventory Management Endpoints
@bp.route('/inventory', methods=['GET'])
def get_inventory():
    """Get current inventory levels."""
    try:
        location = request.args.get('location')
        low_stock = request.args.get('low_stock')  # boolean
        
        query = Inventory.query
        if location:
            query = query.filter(Inventory.location == location)
        if low_stock and low_stock.lower() == 'true':
            query = query.filter(Inventory.quantity_on_hand <= Inventory.reorder_point)
        
        inventory = query.all()
        return jsonify([inv.to_dict() for inv in inventory])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/inventory', methods=['POST'])
def create_inventory():
    """Create inventory record."""
    try:
        data = request.get_json()
        
        inventory = Inventory(
            batch_id=data['batch_id'],
            location=data['location'],
            quantity_on_hand=Decimal(str(data['quantity_on_hand'])),
            reorder_point=Decimal(str(data['reorder_point'])) if data.get('reorder_point') else None
        )
        
        db.session.add(inventory)
        db.session.commit()
        
        return jsonify(inventory.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# Alert Management Endpoints
@bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts."""
    try:
        alert_type = request.args.get('type')
        status = request.args.get('status')
        
        query = Alert.query
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        if status:
            query = query.filter(Alert.status == status)
        
        alerts = query.order_by(Alert.alert_date.desc()).all()
        return jsonify([alert.to_dict() for alert in alerts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/alerts', methods=['POST'])
def create_alert():
    """Create a new alert."""
    try:
        data = request.get_json()
        
        alert = Alert(
            alert_type=data['alert_type'],
            target_id=data['target_id'],
            target_table=data['target_table'],
            message=data['message'],
            threshold_value=Decimal(str(data['threshold_value'])) if data.get('threshold_value') else None,
            status=data.get('status', 'New')
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return jsonify(alert.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@bp.route('/alerts/generate-expiration', methods=['POST'])
def generate_expiration_alerts():
    """Generate expiration alerts for batches expiring soon."""
    try:
        data = request.get_json()
        days_ahead = data.get('days_ahead', 7)  # Default 7 days
        
        from datetime import timedelta
        cutoff_date = datetime.now().date() + timedelta(days=days_ahead)
        
        # Find batches expiring soon
        expiring_batches = Batch.query.filter(
            Batch.expiration_date <= cutoff_date,
            Batch.status == 'In Stock',
            Batch.current_quantity > 0
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
                    message=f'Batch {batch.manufacturer_batch_number} for product {batch.product.product_name} expires on {batch.expiration_date}',
                    threshold_value=batch.current_quantity,
                    status='New'
                )
                db.session.add(alert)
                alerts_created += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Generated {alerts_created} expiration alerts',
            'alerts_created': alerts_created
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/alerts/generate-low-stock', methods=['POST'])
def generate_low_stock_alerts():
    """Generate low stock alerts based on reorder points."""
    try:
        # Find low stock items
        low_stock_inventory = Inventory.query.filter(
            Inventory.quantity_on_hand <= Inventory.reorder_point
        ).all()
        
        alerts_created = 0
        for inv in low_stock_inventory:
            # Check if alert already exists
            existing_alert = Alert.query.filter_by(
                alert_type='Low Stock',
                target_id=inv.inventory_id,
                target_table='Inventory',
                status='New'
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    alert_type='Low Stock',
                    target_id=inv.inventory_id,
                    target_table='Inventory',
                    message=f'Low stock alert: {inv.location} - Quantity: {inv.quantity_on_hand}, Reorder point: {inv.reorder_point}',
                    threshold_value=inv.reorder_point,
                    status='New'
                )
                db.session.add(alert)
                alerts_created += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Generated {alerts_created} low stock alerts',
            'alerts_created': alerts_created
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Analytics Endpoints
@bp.route('/analytics/sales', methods=['GET'])
def get_sales_analytics():
    """Get sales analytics."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = OrderItem.query.join(Order)
        
        if start_date:
            query = query.filter(Order.order_date >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Order.order_date <= datetime.strptime(end_date, '%Y-%m-%d'))
        
        order_items = query.all()
        
        # Calculate analytics
        total_sales = sum(float(item.line_total) for item in order_items)
        total_quantity = sum(float(item.quantity) for item in order_items)
        total_orders = len(set(item.order_id for item in order_items))
        
        # Product-wise sales
        product_sales = {}
        for item in order_items:
            product_name = item.product.product_name
            if product_name not in product_sales:
                product_sales[product_name] = {'quantity': 0, 'revenue': 0}
            product_sales[product_name]['quantity'] += float(item.quantity)
            product_sales[product_name]['revenue'] += float(item.line_total)
        
        # Retailer-wise sales
        retailer_sales = {}
        for item in order_items:
            retailer_name = item.order.retailer.retailer_name
            if retailer_name not in retailer_sales:
                retailer_sales[retailer_name] = {'quantity': 0, 'revenue': 0}
            retailer_sales[retailer_name]['quantity'] += float(item.quantity)
            retailer_sales[retailer_name]['revenue'] += float(item.line_total)
        
        return jsonify({
            'total_sales': total_sales,
            'total_quantity': total_quantity,
            'total_orders': total_orders,
            'average_order_value': total_sales / total_orders if total_orders > 0 else 0,
            'product_sales': product_sales,
            'retailer_sales': retailer_sales
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/analytics/inventory', methods=['GET'])
def get_inventory_analytics():
    """Get inventory analytics."""
    try:
        # Get total inventory value
        inventory_items = Inventory.query.join(Batch).join(Product).all()
        
        total_value = 0
        total_quantity = 0
        low_stock_items = 0
        
        for inv in inventory_items:
            quantity = float(inv.quantity_on_hand)
            mrp = float(inv.batch.product.mrp)
            
            total_quantity += quantity
            total_value += quantity * mrp
            
            if inv.reorder_point and inv.quantity_on_hand <= inv.reorder_point:
                low_stock_items += 1
        
        # Get expiring batches (next 7 days)
        from datetime import timedelta
        cutoff_date = datetime.now().date() + timedelta(days=7)
        expiring_batches = Batch.query.filter(
            Batch.expiration_date <= cutoff_date,
            Batch.status == 'In Stock',
            Batch.current_quantity > 0
        ).count()
        
        return jsonify({
            'total_inventory_value': total_value,
            'total_inventory_quantity': total_quantity,
            'low_stock_items': low_stock_items,
            'expiring_batches_7_days': expiring_batches
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Error handlers
@bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404


@bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400


@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

