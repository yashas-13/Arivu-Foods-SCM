from django.contrib import admin
from .models import Order, OrderItem, SalesTransaction, InventorySnapshot, PerformanceMetric


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'retailer', 'status', 'total_amount', 'order_date', 'created_at']
    list_filter = ['status', 'order_date', 'created_at']
    search_fields = ['order_number', 'retailer__retailer_name']
    readonly_fields = ['order_id', 'order_number', 'created_at', 'updated_at']
    date_hierarchy = 'order_date'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'unit_price', 'line_total']
    list_filter = ['created_at', 'product__category']
    search_fields = ['order__order_number', 'product__product_name']
    readonly_fields = ['created_at', 'updated_at', 'line_total']


@admin.register(SalesTransaction)
class SalesTransactionAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'retailer_name', 'quantity_sold', 'net_sales', 'transaction_date']
    list_filter = ['transaction_date', 'product_category', 'retailer_city']
    search_fields = ['product_name', 'retailer_name', 'batch_number']
    readonly_fields = ['transaction_id', 'created_at']
    date_hierarchy = 'transaction_date'


@admin.register(InventorySnapshot)
class InventorySnapshotAdmin(admin.ModelAdmin):
    list_display = ['product', 'location', 'quantity_on_hand', 'value_on_hand', 'snapshot_date']
    list_filter = ['snapshot_date', 'location']
    search_fields = ['product__product_name', 'location']
    readonly_fields = ['snapshot_id', 'created_at']
    date_hierarchy = 'snapshot_date'


@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'period_type', 'period_start', 'value', 'calculated_at']
    list_filter = ['metric_type', 'period_type', 'calculated_at']
    search_fields = ['metric_type', 'category', 'location']
    readonly_fields = ['metric_id', 'calculated_at']
    date_hierarchy = 'period_start'
