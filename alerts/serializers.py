from rest_framework import serializers
from .models import Alert, AlertRule, AlertSubscription, AlertLog


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model."""
    
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    batch_number = serializers.CharField(source='batch.manufacturer_batch_number', read_only=True)
    retailer_name = serializers.CharField(source='retailer.retailer_name', read_only=True)
    age_in_hours = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ('alert_id', 'created_at', 'updated_at', 'acknowledged_at', 'resolved_at')
    
    def get_age_in_hours(self, obj):
        return obj.age_in_hours()
    
    def get_is_active(self, obj):
        return obj.is_active()


class AlertRuleSerializer(serializers.ModelSerializer):
    """Serializer for AlertRule model."""
    
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    retailer_name = serializers.CharField(source='retailer.retailer_name', read_only=True)
    should_check = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertRule
        fields = '__all__'
        read_only_fields = ('rule_id', 'created_at', 'updated_at', 'last_checked_at')
    
    def get_should_check(self, obj):
        return obj.should_check()


class AlertSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for AlertSubscription model."""
    
    username = serializers.CharField(source='user.username', read_only=True)
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    retailer_name = serializers.CharField(source='retailer.retailer_name', read_only=True)
    
    class Meta:
        model = AlertSubscription
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class AlertLogSerializer(serializers.ModelSerializer):
    """Serializer for AlertLog model."""
    
    alert_title = serializers.CharField(source='alert.title', read_only=True)
    recipient_username = serializers.CharField(source='recipient.username', read_only=True)
    
    class Meta:
        model = AlertLog
        fields = '__all__'
        read_only_fields = ('created_at',)