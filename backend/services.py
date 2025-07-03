"""Business logic services for SCMS operations."""
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func, asc, desc
from .models import db, Product, Batch, Retailer, PricingTier, Order, OrderItem, Inventory, Alert
from decimal import Decimal


class InventoryService:
    """Service for inventory management with FIFO/FEFO logic."""
    
    @staticmethod
    def allocate_inventory(product_id, quantity_needed, method='FEFO'):
        """
        Allocate inventory using FIFO (First In First Out) or FEFO (First Expiry First Out).
        
        Args:
            product_id: ID of the product to allocate
            quantity_needed: Quantity required
            method: 'FIFO' or 'FEFO' (default)
        
        Returns:
            List of allocated batches with quantities
        """
        # Get available batches for the product
        query = db.session.query(Batch, Inventory).join(
            Inventory, Batch.batch_id == Inventory.batch_id
        ).filter(
            and_(
                Batch.product_id == product_id,
                Batch.status == 'In Stock',
                Inventory.quantity_on_hand > 0
            )
        )
        
        # Order by FIFO or FEFO
        if method == 'FEFO':
            query = query.order_by(asc(Batch.expiration_date))
        else:  # FIFO
            query = query.order_by(asc(Batch.production_date))
        
        available_batches = query.all()
        
        if not available_batches:
            return []
        
        allocated_batches = []
        remaining_quantity = quantity_needed
        
        for batch, inventory in available_batches:
            if remaining_quantity <= 0:
                break
            
            available_quantity = min(float(inventory.quantity_on_hand), remaining_quantity)
            
            if available_quantity > 0:
                allocated_batches.append({
                    'batch_id': batch.batch_id,
                    'manufacturer_batch_number': batch.manufacturer_batch_number,
                    'allocated_quantity': available_quantity,
                    'expiration_date': batch.expiration_date.isoformat(),
                    'production_date': batch.production_date.isoformat()
                })
                
                # Update inventory quantities
                inventory.quantity_on_hand -= Decimal(str(available_quantity))
                batch.current_quantity -= Decimal(str(available_quantity))
                
                remaining_quantity -= available_quantity
        
        # Commit the allocation
        if allocated_batches and remaining_quantity <= 0:
            db.session.commit()
            return allocated_batches
        else:
            db.session.rollback()
            return []
    
    @staticmethod
    def get_inventory_status(product_id=None):
        """Get current inventory status."""
        query = db.session.query(
            Product.product_name,
            Product.sku,
            Batch.batch_id,
            Batch.manufacturer_batch_number,
            Batch.expiration_date,
            Inventory.quantity_on_hand,
            Inventory.reorder_point
        ).join(Batch).join(Inventory).join(Product)
        
        if product_id:
            query = query.filter(Product.product_id == product_id)
        
        inventory_data = query.order_by(asc(Batch.expiration_date)).all()
        
        return [{
            'product_name': inv[0],
            'sku': inv[1],
            'batch_id': inv[2],
            'manufacturer_batch_number': inv[3],
            'expiration_date': inv[4].isoformat() if inv[4] else None,
            'quantity_on_hand': float(inv[5]),
            'reorder_point': float(inv[6]) if inv[6] else 0,
            'is_low_stock': float(inv[5]) <= float(inv[6]) if inv[6] else False
        } for inv in inventory_data]


class PricingService:
    """Service for dynamic pricing calculations."""
    
    @staticmethod
    def calculate_price(retailer_id, product_id, quantity):
        """
        Calculate dynamic pricing for a retailer based on their tier and other factors.
        
        Args:
            retailer_id: ID of the retailer
            product_id: ID of the product
            quantity: Quantity being ordered
        
        Returns:
            Dictionary with pricing information
        """
        retailer = Retailer.query.get(retailer_id)
        product = Product.query.get(product_id)
        
        if not retailer or not product:
            return {'error': 'Retailer or product not found'}
        
        base_price = float(product.mrp)
        
        # Get pricing tier
        pricing_tier = retailer.pricing_tier
        if not pricing_tier:
            # Default pricing if no tier assigned
            discount_percentage = 10.0
        else:
            # Use tier-based pricing
            min_discount = float(pricing_tier.min_discount_percentage)
            max_discount = float(pricing_tier.max_discount_percentage)
            
            # Apply volume-based discounts within tier range
            if quantity >= 100:
                discount_percentage = max_discount
            elif quantity >= 50:
                discount_percentage = (min_discount + max_discount) / 2
            else:
                discount_percentage = min_discount
        
        # Calculate prices
        discount_amount = base_price * (discount_percentage / 100)
        discounted_price = base_price - discount_amount
        line_total = discounted_price * quantity
        
        # Check for batch-specific pricing (near expiry)
        batch_discount = PricingService._check_batch_discount(product_id)
        if batch_discount > 0:
            additional_discount = discounted_price * (batch_discount / 100)
            discounted_price -= additional_discount
            line_total = discounted_price * quantity
            discount_percentage += batch_discount
        
        return {
            'base_price': base_price,
            'discount_percentage': discount_percentage,
            'discount_amount': discount_amount,
            'discounted_price': discounted_price,
            'quantity': quantity,
            'line_total': line_total,
            'pricing_tier': pricing_tier.tier_name if pricing_tier else 'Default',
            'has_batch_discount': batch_discount > 0
        }
    
    @staticmethod
    def _check_batch_discount(product_id):
        """Check if there are batches nearing expiry that qualify for additional discount."""
        # Get batches expiring in next 7 days
        near_expiry = Batch.query.filter(
            and_(
                Batch.product_id == product_id,
                Batch.expiration_date <= date.today() + timedelta(days=7),
                Batch.current_quantity > 0
            )
        ).first()
        
        if near_expiry:
            days_to_expiry = (near_expiry.expiration_date - date.today()).days
            if days_to_expiry <= 3:
                return 15.0  # 15% additional discount
            elif days_to_expiry <= 7:
                return 10.0  # 10% additional discount
        
        return 0.0


class AlertService:
    """Service for automated alerts and notifications."""
    
    @staticmethod
    def check_expiration_alerts(days_ahead=7):
        """Check for products nearing expiration."""
        expiring_batches = Batch.query.filter(
            and_(
                Batch.expiration_date <= date.today() + timedelta(days=days_ahead),
                Batch.expiration_date > date.today(),
                Batch.current_quantity > 0,
                Batch.status.in_(['Received', 'In Stock'])
            )
        ).join(Product).order_by(asc(Batch.expiration_date)).all()
        
        alerts = []
        for batch in expiring_batches:
            days_to_expiry = (batch.expiration_date - date.today()).days
            
            # Create or update alert
            existing_alert = Alert.query.filter(
                and_(
                    Alert.alert_type == 'Expiration',
                    Alert.target_id == batch.batch_id,
                    Alert.target_table == 'Batches',
                    Alert.status == 'New'
                )
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    alert_type='Expiration',
                    target_id=batch.batch_id,
                    target_table='Batches',
                    message=f"Batch {batch.manufacturer_batch_number} of {batch.product.product_name} expires in {days_to_expiry} days",
                    threshold_value=days_ahead,
                    alert_date=datetime.utcnow(),
                    status='New'
                )
                db.session.add(alert)
                alerts.append({
                    'batch_id': batch.batch_id,
                    'product_name': batch.product.product_name,
                    'manufacturer_batch_number': batch.manufacturer_batch_number,
                    'expiration_date': batch.expiration_date.isoformat(),
                    'days_to_expiry': days_to_expiry,
                    'current_quantity': float(batch.current_quantity),
                    'severity': 'High' if days_to_expiry <= 3 else 'Medium'
                })
        
        db.session.commit()
        return alerts
    
    @staticmethod
    def check_low_stock_alerts():
        """Check for low stock levels."""
        low_stock_items = db.session.query(
            Product, Inventory, Batch
        ).select_from(Product).join(
            Batch, Product.product_id == Batch.product_id
        ).join(
            Inventory, Batch.batch_id == Inventory.batch_id
        ).filter(
            Inventory.quantity_on_hand <= Inventory.reorder_point
        ).all()
        
        alerts = []
        for product, inventory, batch in low_stock_items:
            # Create or update alert
            existing_alert = Alert.query.filter(
                and_(
                    Alert.alert_type == 'Low Stock',
                    Alert.target_id == product.product_id,
                    Alert.target_table == 'Products',
                    Alert.status == 'New'
                )
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    alert_type='Low Stock',
                    target_id=product.product_id,
                    target_table='Products',
                    message=f"Low stock alert: {product.product_name} (SKU: {product.sku}) is below reorder point",
                    threshold_value=float(inventory.reorder_point) if inventory.reorder_point else 0,
                    alert_date=datetime.utcnow(),
                    status='New'
                )
                db.session.add(alert)
                alerts.append({
                    'product_id': product.product_id,
                    'product_name': product.product_name,
                    'sku': product.sku,
                    'current_stock': float(inventory.quantity_on_hand),
                    'reorder_point': float(inventory.reorder_point) if inventory.reorder_point else 0,
                    'severity': 'High' if inventory.quantity_on_hand == 0 else 'Medium'
                })
        
        db.session.commit()
        return alerts
    
    @staticmethod
    def check_retailer_low_stock_alerts(retailer_id):
        """Check for retailer-specific low stock alerts based on their order patterns."""
        # This would require more complex logic based on retailer's historical orders
        # For now, return a placeholder implementation
        retailer = Retailer.query.get(retailer_id)
        if not retailer:
            return []
        
        # Get retailer's recent orders to infer consumption patterns
        recent_orders = Order.query.filter(
            Order.retailer_id == retailer_id
        ).order_by(desc(Order.order_date)).limit(10).all()
        
        # Simple heuristic: if no orders in last 30 days, they might need stock
        if recent_orders:
            last_order_date = recent_orders[0].order_date
            days_since_last_order = (datetime.utcnow() - last_order_date).days
            
            if days_since_last_order > 30:
                return [{
                    'retailer_id': retailer_id,
                    'retailer_name': retailer.retailer_name,
                    'message': f"Retailer {retailer.retailer_name} hasn't ordered in {days_since_last_order} days",
                    'days_since_last_order': days_since_last_order,
                    'severity': 'Medium'
                }]
        
        return []


class AnalyticsService:
    """Service for analytics and reporting."""
    
    @staticmethod
    def get_sales_summary(start_date=None, end_date=None):
        """Get sales summary for a date range."""
        query = db.session.query(
            func.sum(Order.total_amount).label('total_sales'),
            func.count(Order.order_id).label('total_orders'),
            func.avg(Order.total_amount).label('avg_order_value')
        )
        
        if start_date:
            query = query.filter(Order.order_date >= start_date)
        if end_date:
            query = query.filter(Order.order_date <= end_date)
        
        result = query.first()
        
        return {
            'total_sales': float(result.total_sales) if result.total_sales else 0,
            'total_orders': result.total_orders or 0,
            'avg_order_value': float(result.avg_order_value) if result.avg_order_value else 0
        }
    
    @staticmethod
    def get_inventory_turnover():
        """Calculate inventory turnover metrics."""
        # Simplified calculation - would need more complex logic for accurate turnover
        total_inventory_value = db.session.query(
            func.sum(Inventory.quantity_on_hand * Product.mrp)
        ).join(Batch).join(Product).scalar() or 0
        
        total_sales = db.session.query(func.sum(Order.total_amount)).scalar() or 0
        
        turnover_ratio = float(total_sales) / float(total_inventory_value) if total_inventory_value > 0 else 0
        
        return {
            'total_inventory_value': float(total_inventory_value),
            'total_sales': float(total_sales),
            'turnover_ratio': turnover_ratio
        }