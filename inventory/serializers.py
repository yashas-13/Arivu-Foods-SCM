from rest_framework import serializers
from .models import Product, Batch, Inventory


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('product_id', 'created_at', 'updated_at')


class BatchSerializer(serializers.ModelSerializer):
    """Serializer for Batch model."""
    
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    days_until_expiry = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Batch
        fields = '__all__'
        read_only_fields = ('batch_id', 'created_at', 'updated_at')
    
    def get_days_until_expiry(self, obj):
        return obj.days_until_expiry()
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class InventorySerializer(serializers.ModelSerializer):
    """Serializer for Inventory model."""
    
    product_name = serializers.CharField(source='batch.product.product_name', read_only=True)
    product_sku = serializers.CharField(source='batch.product.sku', read_only=True)
    batch_number = serializers.CharField(source='batch.manufacturer_batch_number', read_only=True)
    expiration_date = serializers.DateField(source='batch.expiration_date', read_only=True)
    is_low_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventory
        fields = '__all__'
        read_only_fields = ('inventory_id', 'last_updated_at')
    
    def get_is_low_stock(self, obj):
        return obj.is_low_stock()