from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from inventory.models import Product, Batch
from pricing.models import Retailer
import uuid

# Create your models here.

class Alert(models.Model):
    """Alert system for expiration, low stock, and other notifications."""
    
    ALERT_TYPES = [
        ('expiry_warning', 'Expiry Warning'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('batch_expired', 'Batch Expired'),
        ('quality_issue', 'Quality Issue'),
        ('reorder_point', 'Reorder Point Reached'),
        ('custom', 'Custom Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    alert_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, help_text="Type of alert")
    title = models.CharField(max_length=255, help_text="Alert title")
    message = models.TextField(help_text="Detailed alert message")
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    
    # Related objects
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alerts', 
                               blank=True, null=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='alerts',
                             blank=True, null=True)
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='alerts',
                                blank=True, null=True)
    
    # Alert metadata
    alert_data = models.JSONField(default=dict, blank=True, help_text="Additional alert data")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    # User who acknowledged/resolved the alert
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                       related_name='acknowledged_alerts',
                                       blank=True, null=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   related_name='resolved_alerts',
                                   blank=True, null=True)
    
    class Meta:
        db_table = 'alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'status']),
            models.Index(fields=['priority', 'created_at']),
        ]
        
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.title}"
    
    def acknowledge(self, user: User = None):
        """Acknowledge the alert."""
        if self.status == 'active':
            self.status = 'acknowledged'
            self.acknowledged_at = timezone.now()
            self.acknowledged_by = user
            self.save()
            
    def resolve(self, user: User = None):
        """Resolve the alert."""
        if self.status in ['active', 'acknowledged']:
            self.status = 'resolved'
            self.resolved_at = timezone.now()
            self.resolved_by = user
            if not self.acknowledged_at:
                self.acknowledged_at = timezone.now()
                self.acknowledged_by = user
            self.save()
            
    def dismiss(self, user: User = None):
        """Dismiss the alert."""
        if self.status in ['active', 'acknowledged']:
            self.status = 'dismissed'
            self.resolved_at = timezone.now()
            self.resolved_by = user
            self.save()
    
    def is_active(self):
        """Check if alert is active."""
        return self.status == 'active'
    
    def age_in_hours(self):
        """Get age of alert in hours."""
        return (timezone.now() - self.created_at).total_seconds() / 3600


class AlertRule(models.Model):
    """Rules for automatic alert generation."""
    
    RULE_TYPES = [
        ('expiry_warning', 'Expiry Warning'),
        ('low_stock', 'Low Stock'),
        ('reorder_point', 'Reorder Point'),
        ('batch_expired', 'Batch Expired'),
    ]
    
    rule_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule_name = models.CharField(max_length=255, help_text="Name of the alert rule")
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES, help_text="Type of alert rule")
    description = models.TextField(blank=True, help_text="Description of the rule")
    
    # Rule parameters
    threshold_days = models.IntegerField(blank=True, null=True, 
                                        help_text="Days threshold for expiry warnings")
    threshold_quantity = models.DecimalField(max_digits=10, decimal_places=2, 
                                            blank=True, null=True,
                                            help_text="Quantity threshold for stock alerts")
    threshold_percentage = models.DecimalField(max_digits=5, decimal_places=2,
                                              blank=True, null=True,
                                              help_text="Percentage threshold for stock alerts")
    
    # Targeting
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alert_rules',
                               blank=True, null=True, help_text="Specific product for this rule")
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='alert_rules',
                                blank=True, null=True, help_text="Specific retailer for this rule")
    
    # Rule settings
    is_active = models.BooleanField(default=True, help_text="Whether rule is active")
    check_frequency_hours = models.IntegerField(default=24, help_text="How often to check this rule (in hours)")
    auto_resolve = models.BooleanField(default=False, help_text="Auto-resolve when condition is no longer met")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_checked_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'alert_rules'
        ordering = ['rule_name']
        
    def __str__(self):
        return f"{self.rule_name} ({self.get_rule_type_display()})"
    
    def should_check(self):
        """Check if rule should be evaluated now."""
        if not self.is_active:
            return False
            
        if not self.last_checked_at:
            return True
            
        hours_since_check = (timezone.now() - self.last_checked_at).total_seconds() / 3600
        return hours_since_check >= self.check_frequency_hours
    
    def update_last_checked(self):
        """Update the last checked timestamp."""
        self.last_checked_at = timezone.now()
        self.save()


class AlertSubscription(models.Model):
    """User subscriptions to different types of alerts."""
    
    NOTIFICATION_METHODS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alert_subscriptions')
    alert_type = models.CharField(max_length=20, choices=Alert.ALERT_TYPES, help_text="Type of alert to subscribe to")
    notification_method = models.CharField(max_length=10, choices=NOTIFICATION_METHODS, 
                                          help_text="How to receive notifications")
    
    # Filtering
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alert_subscriptions',
                               blank=True, null=True, help_text="Subscribe to alerts for specific product")
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='alert_subscriptions',
                                blank=True, null=True, help_text="Subscribe to alerts for specific retailer")
    
    # Settings
    is_active = models.BooleanField(default=True, help_text="Whether subscription is active")
    minimum_priority = models.CharField(max_length=10, choices=Alert.PRIORITY_LEVELS, 
                                       default='medium', help_text="Minimum priority level to receive")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'alert_subscriptions'
        unique_together = ['user', 'alert_type', 'notification_method', 'product', 'retailer']
        
    def __str__(self):
        return f"{self.user.username} - {self.get_alert_type_display()} ({self.get_notification_method_display()})"


class AlertLog(models.Model):
    """Log of alert notifications sent."""
    
    LOG_TYPES = [
        ('generated', 'Alert Generated'),
        ('sent', 'Notification Sent'),
        ('failed', 'Notification Failed'),
        ('acknowledged', 'Alert Acknowledged'),
        ('resolved', 'Alert Resolved'),
    ]
    
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=15, choices=LOG_TYPES, help_text="Type of log entry")
    message = models.TextField(help_text="Log message")
    
    # Notification details
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    notification_method = models.CharField(max_length=10, choices=AlertSubscription.NOTIFICATION_METHODS,
                                          blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'alert_logs'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.alert.title} - {self.get_log_type_display()}"
