from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from inventory.models import Product
import uuid

# Create your models here.

class Retailer(models.Model):
    """Retailer/Customer information."""
    
    retailer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    retailer_name = models.CharField(max_length=255, help_text="Name of the retailer")
    contact_person = models.CharField(max_length=255, blank=True, help_text="Primary contact person")
    email = models.EmailField(blank=True, help_text="Email address")
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number")
    address = models.TextField(blank=True, help_text="Business address")
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True, help_text="Whether retailer is active")
    registration_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'retailers'
        ordering = ['retailer_name']
        
    def __str__(self):
        return self.retailer_name


class PricingTier(models.Model):
    """Pricing tiers for different retailer segments."""
    
    tier_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tier_name = models.CharField(max_length=100, unique=True, help_text="Name of the pricing tier")
    description = models.TextField(blank=True, help_text="Description of the tier")
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Default discount percentage for this tier"
    )
    minimum_order_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True, null=True,
        help_text="Minimum order value to qualify for this tier"
    )
    is_active = models.BooleanField(default=True, help_text="Whether tier is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pricing_tiers'
        ordering = ['tier_name']
        
    def __str__(self):
        return f"{self.tier_name} ({self.discount_percentage}% discount)"


class RetailerPricing(models.Model):
    """Retailer-specific pricing assignments."""
    
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='pricing_assignments')
    pricing_tier = models.ForeignKey(PricingTier, on_delete=models.CASCADE, related_name='retailer_assignments')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='retailer_pricing', blank=True, null=True)
    
    # Override pricing for specific product-retailer combinations
    custom_discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True,
        help_text="Custom discount for this specific product-retailer combination"
    )
    custom_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True, null=True,
        help_text="Custom fixed price for this specific product-retailer combination"
    )
    
    effective_from = models.DateTimeField(default=timezone.now, help_text="When this pricing becomes effective")
    effective_to = models.DateTimeField(blank=True, null=True, help_text="When this pricing expires")
    is_active = models.BooleanField(default=True, help_text="Whether this pricing is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'retailer_pricing'
        unique_together = ['retailer', 'product']
        ordering = ['-effective_from']
        
    def __str__(self):
        product_name = self.product.product_name if self.product else "All Products"
        return f"{self.retailer.retailer_name} - {product_name}"
    
    def get_effective_price(self, base_price=None):
        """Calculate effective price for this retailer-product combination."""
        if not self.is_active:
            return base_price
            
        # Check if pricing is within effective period
        now = timezone.now()
        if self.effective_to and now > self.effective_to:
            return base_price
            
        if self.custom_price:
            return self.custom_price
            
        if base_price is None and self.product:
            base_price = self.product.mrp
            
        if base_price is None:
            return None
            
        # Apply custom discount if available, otherwise use tier discount
        discount = self.custom_discount_percentage or self.pricing_tier.discount_percentage
        
        if discount:
            discount_amount = base_price * (discount / 100)
            return base_price - discount_amount
            
        return base_price


class DynamicPricing(models.Model):
    """Dynamic pricing rules and configurations."""
    
    pricing_rule_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule_name = models.CharField(max_length=255, help_text="Name of the pricing rule")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='dynamic_pricing_rules', blank=True, null=True)
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='dynamic_pricing_rules', blank=True, null=True)
    
    # Batch-specific pricing (for near-expiry products)
    apply_to_expiring_batches = models.BooleanField(default=False, help_text="Apply to batches nearing expiry")
    expiry_threshold_days = models.IntegerField(blank=True, null=True, help_text="Days before expiry to trigger pricing")
    expiry_discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True,
        help_text="Additional discount for expiring batches"
    )
    
    # Volume-based pricing
    volume_tier_quantity = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True, null=True,
        help_text="Minimum quantity for volume discount"
    )
    volume_discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True,
        help_text="Volume discount percentage"
    )
    
    # Time-based pricing
    start_time = models.DateTimeField(blank=True, null=True, help_text="Start time for time-based pricing")
    end_time = models.DateTimeField(blank=True, null=True, help_text="End time for time-based pricing")
    
    is_active = models.BooleanField(default=True, help_text="Whether rule is active")
    priority = models.IntegerField(default=0, help_text="Rule priority (higher number = higher priority)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dynamic_pricing'
        ordering = ['-priority', '-created_at']
        
    def __str__(self):
        return self.rule_name
    
    def is_applicable(self, product=None, retailer=None, batch=None, quantity=None):
        """Check if this pricing rule is applicable."""
        if not self.is_active:
            return False
            
        # Check time constraints
        now = timezone.now()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
            
        # Check product constraint
        if self.product and product and self.product != product:
            return False
            
        # Check retailer constraint
        if self.retailer and retailer and self.retailer != retailer:
            return False
            
        # Check batch expiry constraint
        if self.apply_to_expiring_batches and batch:
            if batch.days_until_expiry() > (self.expiry_threshold_days or 0):
                return False
                
        # Check volume constraint
        if self.volume_tier_quantity and quantity:
            if quantity < self.volume_tier_quantity:
                return False
                
        return True
    
    def calculate_discount(self, base_price, product=None, retailer=None, batch=None, quantity=None):
        """Calculate discount amount based on rule parameters."""
        if not self.is_applicable(product, retailer, batch, quantity):
            return 0
            
        total_discount = 0
        
        # Apply expiry discount
        if self.apply_to_expiring_batches and self.expiry_discount_percentage and batch:
            if batch.days_until_expiry() <= (self.expiry_threshold_days or 0):
                total_discount += base_price * (self.expiry_discount_percentage / 100)
                
        # Apply volume discount
        if self.volume_discount_percentage and quantity and self.volume_tier_quantity:
            if quantity >= self.volume_tier_quantity:
                total_discount += base_price * (self.volume_discount_percentage / 100)
                
        return total_discount
