from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from inventory.models import Product, Batch
from pricing.models import Retailer
import uuid

# Create your models here.

class Order(models.Model):
    """Customer orders from retailers."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('fulfilled', 'Fulfilled'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=100, unique=True, help_text="Human-readable order number")
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='orders')
    
    # Order details
    order_date = models.DateTimeField(default=timezone.now)
    required_date = models.DateTimeField(blank=True, null=True, help_text="Date when order is required")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Financial details
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Shipping information
    shipping_address = models.TextField(blank=True, help_text="Shipping address")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fulfilled_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Order {self.order_number} - {self.retailer.retailer_name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            self.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)
    
    def get_total_items(self):
        """Get total number of items in the order."""
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    def get_total_weight(self):
        """Get total weight of the order."""
        total_weight = 0
        for item in self.items.all():
            if item.product.weight_per_unit:
                total_weight += item.quantity * item.product.weight_per_unit
        return total_weight


class OrderItem(models.Model):
    """Individual items within an order."""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='order_items', blank=True, null=True)
    
    # Quantity and pricing
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    line_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'order_items'
        unique_together = ['order', 'product', 'batch']
        
    def __str__(self):
        return f"{self.order.order_number} - {self.product.product_name} (Qty: {self.quantity})"
    
    def save(self, *args, **kwargs):
        # Calculate line total
        subtotal = self.quantity * self.unit_price
        self.line_total = subtotal - self.discount_amount
        super().save(*args, **kwargs)


class SalesTransaction(models.Model):
    """Detailed sales transaction records for analytics."""
    
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name='sales_transaction')
    
    # Product details at time of sale
    product_sku = models.CharField(max_length=50, help_text="Product SKU at time of sale")
    product_name = models.CharField(max_length=255, help_text="Product name at time of sale")
    product_category = models.CharField(max_length=100, help_text="Product category at time of sale")
    
    # Batch details
    batch_number = models.CharField(max_length=100, help_text="Batch number at time of sale")
    production_date = models.DateField(help_text="Production date of the batch")
    expiration_date = models.DateField(help_text="Expiration date of the batch")
    
    # Retailer details
    retailer_name = models.CharField(max_length=255, help_text="Retailer name at time of sale")
    retailer_city = models.CharField(max_length=100, help_text="Retailer city at time of sale")
    retailer_state = models.CharField(max_length=100, help_text="Retailer state at time of sale")
    
    # Sales details
    quantity_sold = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    net_sales = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Cost and profit
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    # Timestamps
    transaction_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sales_transactions'
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['product_sku', 'transaction_date']),
            models.Index(fields=['retailer_name', 'transaction_date']),
        ]
        
    def __str__(self):
        return f"Sale: {self.product_name} to {self.retailer_name} on {self.transaction_date.date()}"
    
    def save(self, *args, **kwargs):
        # Calculate profit metrics
        if self.cost_per_unit and self.quantity_sold:
            self.total_cost = self.cost_per_unit * self.quantity_sold
            self.gross_profit = self.net_sales - self.total_cost
            if self.net_sales > 0:
                self.profit_margin = (self.gross_profit / self.net_sales) * 100
                
        super().save(*args, **kwargs)


class InventorySnapshot(models.Model):
    """Daily inventory snapshots for trend analysis."""
    
    snapshot_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_snapshots')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='inventory_snapshots', blank=True, null=True)
    location = models.CharField(max_length=255, help_text="Inventory location")
    
    # Snapshot data
    snapshot_date = models.DateField(help_text="Date of the snapshot")
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    value_on_hand = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Additional metrics
    days_until_expiry = models.IntegerField(blank=True, null=True, help_text="Days until expiry for this batch")
    turnover_rate = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, help_text="Inventory turnover rate")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_snapshots'
        unique_together = ['product', 'batch', 'location', 'snapshot_date']
        ordering = ['-snapshot_date']
        
    def __str__(self):
        return f"Inventory Snapshot: {self.product.product_name} - {self.snapshot_date}"


class PerformanceMetric(models.Model):
    """Key performance metrics for analytics dashboard."""
    
    METRIC_TYPES = [
        ('sales_revenue', 'Sales Revenue'),
        ('sales_volume', 'Sales Volume'),
        ('inventory_turnover', 'Inventory Turnover'),
        ('profit_margin', 'Profit Margin'),
        ('customer_acquisition', 'Customer Acquisition'),
        ('order_fulfillment_rate', 'Order Fulfillment Rate'),
        ('waste_percentage', 'Waste Percentage'),
        ('alert_response_time', 'Alert Response Time'),
    ]
    
    PERIOD_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    metric_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    period_type = models.CharField(max_length=15, choices=PERIOD_TYPES)
    period_start = models.DateField(help_text="Start date of the period")
    period_end = models.DateField(help_text="End date of the period")
    
    # Metric value
    value = models.DecimalField(max_digits=15, decimal_places=4, help_text="Metric value")
    previous_value = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, 
                                        help_text="Previous period value for comparison")
    
    # Optional filtering dimensions
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='performance_metrics', blank=True, null=True)
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='performance_metrics', blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, help_text="Product category filter")
    location = models.CharField(max_length=255, blank=True, help_text="Location filter")
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'performance_metrics'
        unique_together = ['metric_type', 'period_type', 'period_start', 'product', 'retailer', 'category', 'location']
        ordering = ['-period_start']
        
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.period_start} to {self.period_end}"
    
    def get_change_percentage(self):
        """Calculate percentage change from previous period."""
        if self.previous_value and self.previous_value != 0:
            return ((self.value - self.previous_value) / self.previous_value) * 100
        return None
    
    def get_trend(self):
        """Get trend direction."""
        change_pct = self.get_change_percentage()
        if change_pct is None:
            return 'no_data'
        elif change_pct > 0:
            return 'up'
        elif change_pct < 0:
            return 'down'
        else:
            return 'stable'
