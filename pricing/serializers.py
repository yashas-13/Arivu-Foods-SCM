from rest_framework import serializers
from .models import Retailer, PricingTier, RetailerPricing, DynamicPricing


class RetailerSerializer(serializers.ModelSerializer):
    """Serializer for Retailer model."""
    
    class Meta:
        model = Retailer
        fields = '__all__'
        read_only_fields = ('retailer_id', 'registration_date', 'created_at', 'updated_at')


class PricingTierSerializer(serializers.ModelSerializer):
    """Serializer for PricingTier model."""
    
    class Meta:
        model = PricingTier
        fields = '__all__'
        read_only_fields = ('tier_id', 'created_at', 'updated_at')


class RetailerPricingSerializer(serializers.ModelSerializer):
    """Serializer for RetailerPricing model."""
    
    retailer_name = serializers.CharField(source='retailer.retailer_name', read_only=True)
    tier_name = serializers.CharField(source='pricing_tier.tier_name', read_only=True)
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    
    class Meta:
        model = RetailerPricing
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class DynamicPricingSerializer(serializers.ModelSerializer):
    """Serializer for DynamicPricing model."""
    
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    retailer_name = serializers.CharField(source='retailer.retailer_name', read_only=True)
    
    class Meta:
        model = DynamicPricing
        fields = '__all__'
        read_only_fields = ('pricing_rule_id', 'created_at', 'updated_at')