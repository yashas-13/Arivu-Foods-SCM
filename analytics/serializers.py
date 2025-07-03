from rest_framework import serializers
from .models import Order, OrderItem, SalesTransaction, InventorySnapshot, PerformanceMetric


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""
    
    retailer_name = serializers.CharField(source='retailer.retailer_name', read_only=True)
    total_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('order_id', 'order_number', 'created_at', 'updated_at')
    
    def get_total_items(self, obj):
        return obj.get_total_items()


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model."""
    
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    batch_number = serializers.CharField(source='batch.manufacturer_batch_number', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'line_total')


class SalesTransactionSerializer(serializers.ModelSerializer):
    """Serializer for SalesTransaction model."""
    
    class Meta:
        model = SalesTransaction
        fields = '__all__'
        read_only_fields = ('transaction_id', 'created_at')


class InventorySnapshotSerializer(serializers.ModelSerializer):
    """Serializer for InventorySnapshot model."""
    
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    
    class Meta:
        model = InventorySnapshot
        fields = '__all__'
        read_only_fields = ('snapshot_id', 'created_at')


class PerformanceMetricSerializer(serializers.ModelSerializer):
    """Serializer for PerformanceMetric model."""
    
    change_percentage = serializers.SerializerMethodField()
    trend = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceMetric
        fields = '__all__'
        read_only_fields = ('metric_id', 'calculated_at')
    
    def get_change_percentage(self, obj):
        return obj.get_change_percentage()
    
    def get_trend(self, obj):
        return obj.get_trend()