from django.contrib import admin
from .models import Product, Batch, Inventory


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'product_name', 'category', 'mrp', 'is_perishable', 'created_at']
    list_filter = ['category', 'is_perishable', 'created_at']
    search_fields = ['product_name', 'sku', 'description']
    readonly_fields = ['product_id', 'created_at', 'updated_at']


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['manufacturer_batch_number', 'product', 'production_date', 'expiration_date', 'current_quantity', 'status']
    list_filter = ['status', 'production_date', 'expiration_date', 'product__category']
    search_fields = ['manufacturer_batch_number', 'product__product_name', 'product__sku']
    readonly_fields = ['batch_id', 'created_at', 'updated_at']
    date_hierarchy = 'production_date'


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['batch', 'location', 'quantity_on_hand', 'reorder_point', 'last_updated_at']
    list_filter = ['location', 'last_updated_at']
    search_fields = ['batch__manufacturer_batch_number', 'batch__product__product_name', 'location']
    readonly_fields = ['inventory_id', 'last_updated_at']
