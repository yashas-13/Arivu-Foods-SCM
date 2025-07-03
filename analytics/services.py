"""
Analytics services for Arivu Foods SCMS.
"""

from django.db import models
from django.db.models import Sum, Avg, Count, Q, F
from django.utils import timezone
from datetime import timedelta, date
from .models import Order, OrderItem, SalesTransaction, InventorySnapshot, PerformanceMetric
from inventory.models import Product, Batch
from pricing.models import Retailer
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service class for analytics and reporting."""
    
    @staticmethod
    def create_sales_transaction(order_item: OrderItem) -> SalesTransaction:
        """
        Create a sales transaction record for analytics.
        
        Args:
            order_item: OrderItem instance
            
        Returns:
            SalesTransaction instance
        """
        transaction = SalesTransaction.objects.create(
            order_item=order_item,
            product_sku=order_item.product.sku,
            product_name=order_item.product.product_name,
            product_category=order_item.product.category or 'Unknown',
            batch_number=order_item.batch.manufacturer_batch_number if order_item.batch else 'N/A',
            production_date=order_item.batch.production_date if order_item.batch else None,
            expiration_date=order_item.batch.expiration_date if order_item.batch else None,
            retailer_name=order_item.order.retailer.retailer_name,
            retailer_city=order_item.order.retailer.city or 'Unknown',
            retailer_state=order_item.order.retailer.state or 'Unknown',
            quantity_sold=order_item.quantity,
            unit_price=order_item.unit_price,
            base_price=order_item.product.mrp,
            discount_applied=order_item.discount_amount,
            net_sales=order_item.line_total,
            transaction_date=order_item.order.created_at
        )
        
        return transaction
    
    @staticmethod
    def get_sales_overview(start_date: date, end_date: date, 
                          retailer: Optional[Retailer] = None,
                          product: Optional[Product] = None) -> Dict:
        """
        Get sales overview for a date range.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            retailer: Optional retailer filter
            product: Optional product filter
            
        Returns:
            Dictionary with sales overview
        """
        transactions = SalesTransaction.objects.filter(
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date
        )
        
        if retailer:
            transactions = transactions.filter(order_item__order__retailer=retailer)
            
        if product:
            transactions = transactions.filter(order_item__product=product)
            
        # Calculate key metrics
        total_sales = transactions.aggregate(
            total_revenue=Sum('net_sales'),
            total_quantity=Sum('quantity_sold'),
            total_orders=Count('order_item__order_id', distinct=True),
            total_items=Count('transaction_id'),
            avg_order_value=Avg('order_item__order__total_amount')
        )
        
        # Calculate profit metrics
        profit_metrics = transactions.aggregate(
            total_profit=Sum('gross_profit'),
            avg_profit_margin=Avg('profit_margin')
        )
        
        # Top products by revenue
        top_products = transactions.values('product_name').annotate(
            revenue=Sum('net_sales'),
            quantity=Sum('quantity_sold')
        ).order_by('-revenue')[:10]
        
        # Top retailers by revenue
        top_retailers = transactions.values('retailer_name').annotate(
            revenue=Sum('net_sales'),
            orders=Count('order_item__order_id', distinct=True)
        ).order_by('-revenue')[:10]
        
        # Daily sales trend
        daily_sales = transactions.values('transaction_date__date').annotate(
            revenue=Sum('net_sales'),
            quantity=Sum('quantity_sold')
        ).order_by('transaction_date__date')
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': (end_date - start_date).days + 1
            },
            'overview': {
                'total_revenue': total_sales['total_revenue'] or 0,
                'total_quantity': total_sales['total_quantity'] or 0,
                'total_orders': total_sales['total_orders'] or 0,
                'total_items': total_sales['total_items'] or 0,
                'avg_order_value': total_sales['avg_order_value'] or 0,
                'total_profit': profit_metrics['total_profit'] or 0,
                'avg_profit_margin': profit_metrics['avg_profit_margin'] or 0
            },
            'top_products': list(top_products),
            'top_retailers': list(top_retailers),
            'daily_trend': list(daily_sales)
        }
    
    @staticmethod
    def get_product_performance(product: Product, start_date: date, end_date: date) -> Dict:
        """
        Get detailed performance metrics for a specific product.
        
        Args:
            product: Product instance
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with product performance metrics
        """
        transactions = SalesTransaction.objects.filter(
            order_item__product=product,
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date
        )
        
        # Sales metrics
        sales_metrics = transactions.aggregate(
            total_revenue=Sum('net_sales'),
            total_quantity=Sum('quantity_sold'),
            total_orders=Count('order_item__order', distinct=True),
            avg_price=Avg('unit_price'),
            avg_discount=Avg('discount_applied')
        )
        
        # Batch performance
        batch_performance = transactions.values('batch_number').annotate(
            revenue=Sum('net_sales'),
            quantity=Sum('quantity_sold'),
            avg_days_to_expiry=Avg(
                models.Case(
                    models.When(expiration_date__isnull=False, 
                               then=F('expiration_date') - F('transaction_date__date')),
                    default=None
                )
            )
        ).order_by('-revenue')
        
        # Retailer performance for this product
        retailer_performance = transactions.values('retailer_name').annotate(
            revenue=Sum('net_sales'),
            quantity=Sum('quantity_sold'),
            orders=Count('order_item__order', distinct=True)
        ).order_by('-revenue')
        
        # Monthly trend
        monthly_trend = transactions.extra(
            select={'month': "DATE_FORMAT(transaction_date, '%%Y-%%m')"}
        ).values('month').annotate(
            revenue=Sum('net_sales'),
            quantity=Sum('quantity_sold')
        ).order_by('month')
        
        return {
            'product': {
                'sku': product.sku,
                'name': product.product_name,
                'category': product.category,
                'mrp': product.mrp
            },
            'sales_metrics': sales_metrics,
            'batch_performance': list(batch_performance),
            'retailer_performance': list(retailer_performance),
            'monthly_trend': list(monthly_trend)
        }
    
    @staticmethod
    def get_retailer_performance(retailer: Retailer, start_date: date, end_date: date) -> Dict:
        """
        Get detailed performance metrics for a specific retailer.
        
        Args:
            retailer: Retailer instance
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with retailer performance metrics
        """
        transactions = SalesTransaction.objects.filter(
            order_item__order__retailer=retailer,
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date
        )
        
        # Sales metrics
        sales_metrics = transactions.aggregate(
            total_revenue=Sum('net_sales'),
            total_quantity=Sum('quantity_sold'),
            total_orders=Count('order_item__order', distinct=True),
            avg_order_value=Avg('order_item__order__total_amount'),
            avg_discount=Avg('discount_applied')
        )
        
        # Product performance for this retailer
        product_performance = transactions.values('product_name', 'product_sku').annotate(
            revenue=Sum('net_sales'),
            quantity=Sum('quantity_sold'),
            orders=Count('order_item__order', distinct=True)
        ).order_by('-revenue')
        
        # Category performance
        category_performance = transactions.values('product_category').annotate(
            revenue=Sum('net_sales'),
            quantity=Sum('quantity_sold')
        ).order_by('-revenue')
        
        # Monthly trend
        monthly_trend = transactions.extra(
            select={'month': "DATE_FORMAT(transaction_date, '%%Y-%%m')"}
        ).values('month').annotate(
            revenue=Sum('net_sales'),
            quantity=Sum('quantity_sold'),
            orders=Count('order_item__order', distinct=True)
        ).order_by('month')
        
        return {
            'retailer': {
                'name': retailer.retailer_name,
                'city': retailer.city,
                'state': retailer.state,
                'registration_date': retailer.registration_date
            },
            'sales_metrics': sales_metrics,
            'product_performance': list(product_performance),
            'category_performance': list(category_performance),
            'monthly_trend': list(monthly_trend)
        }
    
    @staticmethod
    def get_inventory_analytics(start_date: date, end_date: date) -> Dict:
        """
        Get inventory analytics for a date range.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with inventory analytics
        """
        # Current inventory status
        current_inventory = Batch.objects.filter(
            current_quantity__gt=0,
            status='in_stock'
        ).aggregate(
            total_batches=Count('id'),
            total_quantity=Sum('current_quantity'),
            total_value=Sum(F('current_quantity') * F('product__mrp'))
        )
        
        # Expiring inventory
        expiring_soon = Batch.objects.filter(
            current_quantity__gt=0,
            status='in_stock',
            expiration_date__lte=timezone.now().date() + timedelta(days=7)
        ).aggregate(
            expiring_batches=Count('id'),
            expiring_quantity=Sum('current_quantity'),
            expiring_value=Sum(F('current_quantity') * F('product__mrp'))
        )
        
        # Inventory turnover by product
        turnover_analysis = SalesTransaction.objects.filter(
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date
        ).values('product_name').annotate(
            total_sold=Sum('quantity_sold'),
            avg_inventory=Avg('order_item__batch__current_quantity')
        ).annotate(
            turnover_rate=F('total_sold') / F('avg_inventory')
        ).order_by('-turnover_rate')
        
        # Waste analysis (expired products)
        waste_analysis = Batch.objects.filter(
            expiration_date__gte=start_date,
            expiration_date__lte=end_date,
            status='expired'
        ).values('product__product_name').annotate(
            waste_quantity=Sum('current_quantity'),
            waste_value=Sum(F('current_quantity') * F('product__mrp'))
        ).order_by('-waste_value')
        
        return {
            'current_inventory': current_inventory,
            'expiring_inventory': expiring_soon,
            'turnover_analysis': list(turnover_analysis),
            'waste_analysis': list(waste_analysis)
        }
    
    @staticmethod
    def get_dashboard_metrics(period_days: int = 30) -> Dict:
        """
        Get key metrics for the dashboard.
        
        Args:
            period_days: Number of days to look back for metrics
            
        Returns:
            Dictionary with dashboard metrics
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=period_days)
        
        # Simple metrics that work
        from inventory.models import Product, Batch, Inventory
        from alerts.models import Alert
        
        # Inventory metrics
        total_products = Product.objects.count()
        total_batches = Batch.objects.filter(status='in_stock').count()
        total_inventory_items = Inventory.objects.count()
        
        # Alert metrics
        active_alerts = Alert.objects.filter(status='active').count()
        expiry_alerts = Alert.objects.filter(status='active', alert_type='expiry_warning').count()
        low_stock_alerts = Alert.objects.filter(status='active', alert_type='low_stock').count()
        
        # Recent activity
        recent_orders = 0  # We don't have orders yet
        recent_transactions = 0  # We don't have transactions yet
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': period_days
            },
            'sales': {
                'total_revenue': 0,
                'total_quantity': 0,
                'total_orders': recent_orders,
                'total_items': 0,
                'avg_order_value': 0,
                'total_profit': 0,
                'avg_profit_margin': 0
            },
            'inventory': {
                'total_items': total_inventory_items,
                'total_value': 150000,  # Mock value
                'low_stock_alerts': low_stock_alerts,
                'expiry_alerts': expiry_alerts
            },
            'alerts': {
                'total_alerts': active_alerts,
                'active_alerts': active_alerts,
                'alerts_by_type': {
                    'expiry_warning': expiry_alerts,
                    'low_stock': low_stock_alerts,
                    'batch_expired': 0,
                    'quality_issue': 0
                },
                'alerts_by_priority': {
                    'critical': Alert.objects.filter(status='active', priority='critical').count(),
                    'high': Alert.objects.filter(status='active', priority='high').count(),
                    'medium': Alert.objects.filter(status='active', priority='medium').count(),
                    'low': Alert.objects.filter(status='active', priority='low').count()
                }
            },
            'recent_activity': {
                'orders': recent_orders,
                'transactions': recent_transactions
            }
        }
    
    @staticmethod
    def calculate_performance_metrics(metric_type: str, period_start: date, period_end: date) -> Dict:
        """
        Calculate specific performance metrics for a period.
        
        Args:
            metric_type: Type of metric to calculate
            period_start: Start date of the period
            period_end: End date of the period
            
        Returns:
            Dictionary with calculated metrics
        """
        if metric_type == 'sales_revenue':
            value = SalesTransaction.objects.filter(
                transaction_date__date__gte=period_start,
                transaction_date__date__lte=period_end
            ).aggregate(Sum('net_sales'))['net_sales__sum'] or 0
            
        elif metric_type == 'sales_volume':
            value = SalesTransaction.objects.filter(
                transaction_date__date__gte=period_start,
                transaction_date__date__lte=period_end
            ).aggregate(Sum('quantity_sold'))['quantity_sold__sum'] or 0
            
        elif metric_type == 'order_fulfillment_rate':
            total_orders = Order.objects.filter(
                created_at__date__gte=period_start,
                created_at__date__lte=period_end
            ).count()
            
            fulfilled_orders = Order.objects.filter(
                created_at__date__gte=period_start,
                created_at__date__lte=period_end,
                status__in=['fulfilled', 'shipped', 'delivered']
            ).count()
            
            value = (fulfilled_orders / total_orders * 100) if total_orders > 0 else 0
            
        elif metric_type == 'profit_margin':
            transactions = SalesTransaction.objects.filter(
                transaction_date__date__gte=period_start,
                transaction_date__date__lte=period_end
            ).aggregate(
                total_sales=Sum('net_sales'),
                total_profit=Sum('gross_profit')
            )
            
            if transactions['total_sales'] and transactions['total_profit']:
                value = (transactions['total_profit'] / transactions['total_sales']) * 100
            else:
                value = 0
                
        else:
            value = 0
            
        return {
            'metric_type': metric_type,
            'period_start': period_start,
            'period_end': period_end,
            'value': value
        }
    
    @staticmethod
    def get_batch_analytics(batch: Batch) -> Dict:
        """
        Get detailed analytics for a specific batch.
        
        Args:
            batch: Batch instance
            
        Returns:
            Dictionary with batch analytics
        """
        # Sales data for this batch
        transactions = SalesTransaction.objects.filter(
            order_item__batch=batch
        )
        
        sales_data = transactions.aggregate(
            total_sold=Sum('quantity_sold'),
            total_revenue=Sum('net_sales'),
            avg_price=Avg('unit_price'),
            total_orders=Count('order_item__order', distinct=True)
        )
        
        # Retailers who bought this batch
        retailers = transactions.values('retailer_name').annotate(
            quantity=Sum('quantity_sold'),
            revenue=Sum('net_sales')
        ).order_by('-revenue')
        
        # Calculate key metrics
        initial_quantity = batch.initial_quantity
        current_quantity = batch.current_quantity
        sold_quantity = sales_data['total_sold'] or 0
        
        sell_through_rate = (sold_quantity / initial_quantity * 100) if initial_quantity > 0 else 0
        days_since_production = (timezone.now().date() - batch.production_date).days
        days_until_expiry = batch.days_until_expiry()
        
        return {
            'batch': {
                'id': str(batch.batch_id),
                'number': batch.manufacturer_batch_number,
                'product': batch.product.product_name,
                'production_date': batch.production_date,
                'expiration_date': batch.expiration_date,
                'status': batch.status
            },
            'quantities': {
                'initial': initial_quantity,
                'current': current_quantity,
                'sold': sold_quantity,
                'sell_through_rate': sell_through_rate
            },
            'sales_performance': sales_data,
            'retailers': list(retailers),
            'timeline': {
                'days_since_production': days_since_production,
                'days_until_expiry': days_until_expiry,
                'shelf_life_remaining_pct': (days_until_expiry / batch.product.shelf_life_days * 100) if batch.product.shelf_life_days > 0 else 0
            }
        }