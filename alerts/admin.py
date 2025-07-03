from django.contrib import admin
from .models import Alert, AlertRule, AlertSubscription, AlertLog


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'alert_type', 'priority', 'status', 'product', 'created_at']
    list_filter = ['alert_type', 'priority', 'status', 'created_at']
    search_fields = ['title', 'message', 'product__product_name']
    readonly_fields = ['alert_id', 'created_at', 'updated_at', 'acknowledged_at', 'resolved_at']
    date_hierarchy = 'created_at'


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ['rule_name', 'rule_type', 'is_active', 'check_frequency_hours', 'last_checked_at']
    list_filter = ['rule_type', 'is_active', 'created_at']
    search_fields = ['rule_name', 'description']
    readonly_fields = ['rule_id', 'created_at', 'updated_at', 'last_checked_at']


@admin.register(AlertSubscription)
class AlertSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'alert_type', 'notification_method', 'minimum_priority', 'is_active']
    list_filter = ['alert_type', 'notification_method', 'minimum_priority', 'is_active']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AlertLog)
class AlertLogAdmin(admin.ModelAdmin):
    list_display = ['alert', 'log_type', 'recipient', 'notification_method', 'created_at']
    list_filter = ['log_type', 'notification_method', 'created_at']
    search_fields = ['alert__title', 'message', 'recipient__username']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
