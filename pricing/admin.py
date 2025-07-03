from django.contrib import admin
from .models import Retailer, PricingTier, RetailerPricing, DynamicPricing


@admin.register(Retailer)
class RetailerAdmin(admin.ModelAdmin):
    list_display = ['retailer_name', 'contact_person', 'email', 'city', 'state', 'is_active', 'registration_date']
    list_filter = ['is_active', 'city', 'state', 'registration_date']
    search_fields = ['retailer_name', 'contact_person', 'email', 'phone']
    readonly_fields = ['retailer_id', 'registration_date', 'created_at', 'updated_at']


@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ['tier_name', 'discount_percentage', 'minimum_order_value', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['tier_name', 'description']
    readonly_fields = ['tier_id', 'created_at', 'updated_at']


@admin.register(RetailerPricing)
class RetailerPricingAdmin(admin.ModelAdmin):
    list_display = ['retailer', 'pricing_tier', 'product', 'custom_discount_percentage', 'is_active', 'effective_from']
    list_filter = ['is_active', 'effective_from', 'pricing_tier']
    search_fields = ['retailer__retailer_name', 'product__product_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DynamicPricing)
class DynamicPricingAdmin(admin.ModelAdmin):
    list_display = ['rule_name', 'product', 'retailer', 'priority', 'is_active']
    list_filter = ['is_active', 'priority', 'apply_to_expiring_batches']
    search_fields = ['rule_name', 'product__product_name', 'retailer__retailer_name']
    readonly_fields = ['pricing_rule_id', 'created_at', 'updated_at']
