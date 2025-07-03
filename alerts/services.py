"""
Alert management services for Arivu Foods SCMS.
"""

from django.db import transaction
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Alert, AlertRule, AlertSubscription, AlertLog
from inventory.models import Product, Batch, Inventory
from pricing.models import Retailer
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """Service class for managing alerts and notifications."""
    
    @staticmethod
    def create_alert(alert_type: str, title: str, message: str, 
                    priority: str = 'medium', product: Optional[Product] = None,
                    batch: Optional[Batch] = None, retailer: Optional[Retailer] = None,
                    alert_data: Optional[Dict] = None) -> Alert:
        """
        Create a new alert.
        
        Args:
            alert_type: Type of alert
            title: Alert title
            message: Alert message
            priority: Alert priority
            product: Optional product reference
            batch: Optional batch reference
            retailer: Optional retailer reference
            alert_data: Optional additional data
            
        Returns:
            Alert instance
        """
        alert = Alert.objects.create(
            alert_type=alert_type,
            title=title,
            message=message,
            priority=priority,
            product=product,
            batch=batch,
            retailer=retailer,
            alert_data=alert_data or {}
        )
        
        # Log alert creation
        AlertLog.objects.create(
            alert=alert,
            log_type='generated',
            message=f"Alert created: {title}"
        )
        
        # Send notifications
        AlertService.send_notifications(alert)
        
        return alert
    
    @staticmethod
    def check_expiry_alerts(days_ahead: int = 7) -> List[Alert]:
        """
        Check for products expiring within specified days and create alerts.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of created alerts
        """
        alerts_created = []
        
        # Get expiring batches
        from inventory.services import InventoryService
        expiring_batches = InventoryService.get_expiring_batches(days_ahead)
        
        for batch in expiring_batches:
            # Check if alert already exists for this batch
            existing_alert = Alert.objects.filter(
                alert_type='expiry_warning',
                batch=batch,
                status='active'
            ).first()
            
            if existing_alert:
                continue
                
            days_until_expiry = batch.days_until_expiry()
            
            if days_until_expiry <= 1:
                priority = 'critical'
                title = f"URGENT: {batch.product.product_name} expires tomorrow"
            elif days_until_expiry <= 3:
                priority = 'high'
                title = f"HIGH: {batch.product.product_name} expires in {days_until_expiry} days"
            else:
                priority = 'medium'
                title = f"WARNING: {batch.product.product_name} expires in {days_until_expiry} days"
                
            message = (
                f"Batch {batch.manufacturer_batch_number} of {batch.product.product_name} "
                f"will expire on {batch.expiration_date.strftime('%Y-%m-%d')}. "
                f"Current quantity: {batch.current_quantity} {batch.product.unit_of_measure}. "
                f"Consider applying discount or accelerating sales."
            )
            
            alert = AlertService.create_alert(
                alert_type='expiry_warning',
                title=title,
                message=message,
                priority=priority,
                product=batch.product,
                batch=batch,
                alert_data={
                    'days_until_expiry': days_until_expiry,
                    'current_quantity': float(batch.current_quantity),
                    'expiration_date': batch.expiration_date.isoformat()
                }
            )
            
            alerts_created.append(alert)
            
        return alerts_created
    
    @staticmethod
    def check_low_stock_alerts() -> List[Alert]:
        """
        Check for low stock conditions and create alerts.
        
        Returns:
            List of created alerts
        """
        alerts_created = []
        
        # Get low stock inventory
        from inventory.services import InventoryService
        low_stock_items = InventoryService.get_low_stock_alerts()
        
        for item in low_stock_items:
            # Check if alert already exists for this inventory item
            existing_alert = Alert.objects.filter(
                alert_type='low_stock',
                product=item['product'],
                batch=item['batch'],
                status='active'
            ).first()
            
            if existing_alert:
                continue
                
            deficit = item['deficit']
            
            if deficit >= item['current_quantity']:
                priority = 'critical'
                title = f"CRITICAL: {item['product'].product_name} critically low"
            elif deficit >= item['reorder_point'] * 0.5:
                priority = 'high'
                title = f"HIGH: {item['product'].product_name} low stock"
            else:
                priority = 'medium'
                title = f"WARNING: {item['product'].product_name} approaching reorder point"
                
            message = (
                f"Product {item['product'].product_name} at {item['location']} "
                f"has {item['current_quantity']} units remaining. "
                f"Reorder point is {item['reorder_point']} units. "
                f"Deficit: {deficit} units. Please reorder immediately."
            )
            
            alert = AlertService.create_alert(
                alert_type='low_stock',
                title=title,
                message=message,
                priority=priority,
                product=item['product'],
                batch=item['batch'],
                alert_data={
                    'location': item['location'],
                    'current_quantity': float(item['current_quantity']),
                    'reorder_point': float(item['reorder_point']),
                    'deficit': float(deficit)
                }
            )
            
            alerts_created.append(alert)
            
        return alerts_created
    
    @staticmethod
    def check_expired_batches() -> List[Alert]:
        """
        Check for expired batches and create alerts.
        
        Returns:
            List of created alerts
        """
        alerts_created = []
        
        # Get expired batches
        expired_batches = Batch.objects.filter(
            expiration_date__lt=timezone.now().date(),
            current_quantity__gt=0,
            status='in_stock'
        )
        
        for batch in expired_batches:
            # Check if alert already exists for this batch
            existing_alert = Alert.objects.filter(
                alert_type='batch_expired',
                batch=batch,
                status='active'
            ).first()
            
            if existing_alert:
                continue
                
            # Update batch status to expired
            batch.status = 'expired'
            batch.save()
            
            title = f"EXPIRED: {batch.product.product_name} batch expired"
            message = (
                f"Batch {batch.manufacturer_batch_number} of {batch.product.product_name} "
                f"expired on {batch.expiration_date.strftime('%Y-%m-%d')}. "
                f"Quantity: {batch.current_quantity} {batch.product.unit_of_measure}. "
                f"Please remove from inventory immediately."
            )
            
            alert = AlertService.create_alert(
                alert_type='batch_expired',
                title=title,
                message=message,
                priority='critical',
                product=batch.product,
                batch=batch,
                alert_data={
                    'expiration_date': batch.expiration_date.isoformat(),
                    'expired_quantity': float(batch.current_quantity)
                }
            )
            
            alerts_created.append(alert)
            
        return alerts_created
    
    @staticmethod
    def send_notifications(alert: Alert):
        """
        Send notifications for an alert based on user subscriptions.
        
        Args:
            alert: Alert instance
        """
        # Get relevant subscriptions
        subscriptions = AlertSubscription.objects.filter(
            alert_type=alert.alert_type,
            is_active=True
        )
        
        # Filter by product if specified
        if alert.product:
            subscriptions = subscriptions.filter(
                models.Q(product__isnull=True) | models.Q(product=alert.product)
            )
            
        # Filter by retailer if specified
        if alert.retailer:
            subscriptions = subscriptions.filter(
                models.Q(retailer__isnull=True) | models.Q(retailer=alert.retailer)
            )
            
        # Filter by minimum priority
        priority_levels = ['low', 'medium', 'high', 'critical']
        alert_priority_index = priority_levels.index(alert.priority)
        
        for subscription in subscriptions:
            min_priority_index = priority_levels.index(subscription.minimum_priority)
            
            if alert_priority_index >= min_priority_index:
                AlertService.send_notification(alert, subscription)
    
    @staticmethod
    def send_notification(alert: Alert, subscription: AlertSubscription):
        """
        Send a single notification.
        
        Args:
            alert: Alert instance
            subscription: AlertSubscription instance
        """
        try:
            # In a real implementation, this would send actual notifications
            # For now, we'll just log the notification
            
            if subscription.notification_method == 'email':
                # Send email notification
                logger.info(f"Sending email notification to {subscription.user.email} for alert {alert.title}")
                
            elif subscription.notification_method == 'sms':
                # Send SMS notification
                logger.info(f"Sending SMS notification for alert {alert.title}")
                
            elif subscription.notification_method == 'push':
                # Send push notification
                logger.info(f"Sending push notification for alert {alert.title}")
                
            elif subscription.notification_method == 'in_app':
                # Create in-app notification
                logger.info(f"Creating in-app notification for alert {alert.title}")
                
            # Log successful notification
            AlertLog.objects.create(
                alert=alert,
                log_type='sent',
                message=f"Notification sent via {subscription.notification_method}",
                recipient=subscription.user,
                notification_method=subscription.notification_method
            )
            
        except Exception as e:
            logger.error(f"Failed to send notification for alert {alert.title}: {str(e)}")
            
            # Log failed notification
            AlertLog.objects.create(
                alert=alert,
                log_type='failed',
                message=f"Failed to send notification via {subscription.notification_method}: {str(e)}",
                recipient=subscription.user,
                notification_method=subscription.notification_method
            )
    
    @staticmethod
    def run_alert_checks():
        """
        Run all alert checks based on active alert rules.
        
        Returns:
            Dictionary with check results
        """
        results = {
            'expiry_alerts': [],
            'low_stock_alerts': [],
            'expired_batch_alerts': [],
            'total_alerts_created': 0
        }
        
        # Check expiry alerts
        results['expiry_alerts'] = AlertService.check_expiry_alerts()
        
        # Check low stock alerts
        results['low_stock_alerts'] = AlertService.check_low_stock_alerts()
        
        # Check expired batches
        results['expired_batch_alerts'] = AlertService.check_expired_batches()
        
        # Calculate total
        results['total_alerts_created'] = (
            len(results['expiry_alerts']) +
            len(results['low_stock_alerts']) +
            len(results['expired_batch_alerts'])
        )
        
        return results
    
    @staticmethod
    def get_active_alerts(user: Optional[User] = None, alert_type: Optional[str] = None,
                         priority: Optional[str] = None) -> List[Alert]:
        """
        Get active alerts with optional filtering.
        
        Args:
            user: Optional user filter (based on subscriptions)
            alert_type: Optional alert type filter
            priority: Optional priority filter
            
        Returns:
            List of active alerts
        """
        alerts = Alert.objects.filter(status='active')
        
        if alert_type:
            alerts = alerts.filter(alert_type=alert_type)
            
        if priority:
            alerts = alerts.filter(priority=priority)
            
        if user:
            # Filter based on user subscriptions
            subscribed_types = AlertSubscription.objects.filter(
                user=user,
                is_active=True
            ).values_list('alert_type', flat=True)
            
            alerts = alerts.filter(alert_type__in=subscribed_types)
            
        return list(alerts.order_by('-created_at'))
    
    @staticmethod
    def get_alert_summary() -> Dict:
        """
        Get alert summary statistics.
        
        Returns:
            Dictionary with alert statistics
        """
        total_alerts = Alert.objects.count()
        active_alerts = Alert.objects.filter(status='active').count()
        
        alerts_by_type = {}
        for alert_type, _ in Alert.ALERT_TYPES:
            count = Alert.objects.filter(
                alert_type=alert_type,
                status='active'
            ).count()
            alerts_by_type[alert_type] = count
            
        alerts_by_priority = {}
        for priority, _ in Alert.PRIORITY_LEVELS:
            count = Alert.objects.filter(
                priority=priority,
                status='active'
            ).count()
            alerts_by_priority[priority] = count
            
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'alerts_by_type': alerts_by_type,
            'alerts_by_priority': alerts_by_priority,
            'resolved_alerts': Alert.objects.filter(status='resolved').count(),
            'dismissed_alerts': Alert.objects.filter(status='dismissed').count()
        }