from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta
import uuid

# Create your models here.

class Product(models.Model):
    """Master product data for all food products."""
    
    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit")
    upc_ean = models.CharField(max_length=20, unique=True, blank=True, null=True, 
                              help_text="Universal Product Code / European Article Number")
    product_name = models.CharField(max_length=255, help_text="Name of the product")
    description = models.TextField(blank=True, help_text="Detailed description")
    category = models.CharField(max_length=100, blank=True, help_text="Product category")
    brand = models.CharField(max_length=100, blank=True, help_text="Brand name")
    mrp = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
                             help_text="Manufacturer's Recommended Price per unit")
    weight_per_unit = models.DecimalField(max_digits=10, decimal_places=3, 
                                         validators=[MinValueValidator(0)], blank=True, null=True,
                                         help_text="Weight of a single unit (e.g., in kg)")
    unit_of_measure = models.CharField(max_length=20, blank=True, 
                                      help_text="Unit type (e.g., kg, dozen, pouch)")
    shelf_life_days = models.IntegerField(validators=[MinValueValidator(0)],
                                         help_text="Standard shelf life in days from production")
    storage_requirements = models.CharField(max_length=255, blank=True,
                                           help_text="Storage requirements (e.g., Refrigerated)")
    is_perishable = models.BooleanField(default=True, help_text="Indicates if product is perishable")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        ordering = ['product_name']
        
    def __str__(self):
        return f"{self.product_name} ({self.sku})"
    
    def get_expiry_date(self, production_date):
        """Calculate expiry date based on production date and shelf life."""
        return production_date + timedelta(days=self.shelf_life_days)


class Batch(models.Model):
    """Tracks specific production batches for traceability and expiration management."""
    
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('in_stock', 'In Stock'),
        ('dispatched', 'Dispatched'),
        ('expired', 'Expired'),
        ('recalled', 'Recalled'),
    ]
    
    batch_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    manufacturer_batch_number = models.CharField(max_length=100, 
                                                help_text="Batch number from manufacturer")
    production_date = models.DateField(help_text="Date the batch was produced")
    expiration_date = models.DateField(help_text="Date the batch expires")
    initial_quantity = models.DecimalField(max_digits=10, decimal_places=2,
                                          validators=[MinValueValidator(0)],
                                          help_text="Quantity received from manufacturer")
    current_quantity = models.DecimalField(max_digits=10, decimal_places=2,
                                          validators=[MinValueValidator(0)],
                                          help_text="Current available quantity")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    manufacturing_location = models.CharField(max_length=255, blank=True,
                                             help_text="Location where batch was manufactured")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'batches'
        ordering = ['-production_date']
        unique_together = ['product', 'manufacturer_batch_number']
        
    def __str__(self):
        return f"{self.product.product_name} - Batch {self.manufacturer_batch_number}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate expiration date if not provided."""
        if not self.expiration_date:
            self.expiration_date = self.product.get_expiry_date(self.production_date)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if batch is expired."""
        return timezone.now().date() > self.expiration_date
    
    def days_until_expiry(self):
        """Calculate days until expiry."""
        return (self.expiration_date - timezone.now().date()).days
    
    def quantity_available(self):
        """Get available quantity for FIFO/FEFO logic."""
        return self.current_quantity
    
    def can_fulfill_quantity(self, requested_quantity):
        """Check if batch can fulfill requested quantity."""
        return self.current_quantity >= requested_quantity
    
    def allocate_quantity(self, quantity):
        """Allocate quantity from batch (FIFO/FEFO logic)."""
        if self.can_fulfill_quantity(quantity):
            self.current_quantity -= quantity
            self.save()
            return True
        return False


class Inventory(models.Model):
    """Tracks stock levels for batches in different locations."""
    
    inventory_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='inventory_records')
    location = models.CharField(max_length=255, help_text="Physical location of inventory")
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2,
                                          validators=[MinValueValidator(0)],
                                          help_text="Current quantity at this location")
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2,
                                       validators=[MinValueValidator(0)], blank=True, null=True,
                                       help_text="Quantity threshold for replenishment alert")
    last_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory'
        ordering = ['location', 'batch__expiration_date']
        unique_together = ['batch', 'location']
        
    def __str__(self):
        return f"{self.batch} - {self.location}: {self.quantity_on_hand}"
    
    def is_low_stock(self):
        """Check if inventory is below reorder point."""
        if self.reorder_point:
            return self.quantity_on_hand <= self.reorder_point
        return False
