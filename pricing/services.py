"""
Dynamic pricing services for Arivu Foods SCMS.
"""

from django.db import models
from django.utils import timezone
from .models import Retailer, PricingTier, RetailerPricing, DynamicPricing
from inventory.models import Product, Batch
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class PricingService:
    """Service class for managing dynamic pricing logic."""
    
    @staticmethod
    def get_retailer_price(retailer: Retailer, product: Product, quantity: float = 1, 
                          batch: Optional[Batch] = None) -> Dict:
        """
        Calculate the final price for a retailer-product combination.
        
        Args:
            retailer: Retailer instance
            product: Product instance
            quantity: Quantity being purchased
            batch: Optional batch instance for batch-specific pricing
            
        Returns:
            Dictionary with pricing details
        """
        base_price = product.mrp
        final_price = base_price
        applied_discounts = []
        
        # Get retailer-specific pricing
        retailer_pricing = RetailerPricing.objects.filter(
            retailer=retailer,
            product=product,
            is_active=True,
            effective_from__lte=timezone.now()
        ).filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gt=timezone.now())
        ).first()
        
        if not retailer_pricing:
            # Fall back to tier-based pricing
            retailer_pricing = RetailerPricing.objects.filter(
                retailer=retailer,
                product__isnull=True,  # General tier assignment
                is_active=True,
                effective_from__lte=timezone.now()
            ).filter(
                models.Q(effective_to__isnull=True) | models.Q(effective_to__gt=timezone.now())
            ).first()
        
        if retailer_pricing:
            final_price = retailer_pricing.get_effective_price(base_price)
            tier_discount = base_price - final_price
            if tier_discount > 0:
                applied_discounts.append({
                    'type': 'tier_discount',
                    'name': retailer_pricing.pricing_tier.tier_name,
                    'discount_amount': tier_discount,
                    'discount_percentage': (tier_discount / base_price) * 100
                })
        
        # Apply dynamic pricing rules
        dynamic_rules = DynamicPricing.objects.filter(
            is_active=True
        ).filter(
            models.Q(product__isnull=True) | models.Q(product=product)
        ).filter(
            models.Q(retailer__isnull=True) | models.Q(retailer=retailer)
        ).order_by('-priority')
        
        for rule in dynamic_rules:
            if rule.is_applicable(product, retailer, batch, quantity):
                discount = rule.calculate_discount(final_price, product, retailer, batch, quantity)
                if discount > 0:
                    final_price -= discount
                    applied_discounts.append({
                        'type': 'dynamic_discount',
                        'name': rule.rule_name,
                        'discount_amount': discount,
                        'discount_percentage': (discount / base_price) * 100
                    })
        
        total_discount = base_price - final_price
        
        return {
            'base_price': base_price,
            'final_price': final_price,
            'total_discount': total_discount,
            'total_discount_percentage': (total_discount / base_price) * 100,
            'applied_discounts': applied_discounts,
            'retailer': retailer.retailer_name,
            'product': product.product_name,
            'quantity': quantity,
            'batch': batch.manufacturer_batch_number if batch else None
        }
    
    @staticmethod
    def get_bulk_pricing(retailer: Retailer, product_quantities: List[tuple]) -> List[Dict]:
        """
        Calculate pricing for multiple products in bulk.
        
        Args:
            retailer: Retailer instance
            product_quantities: List of (product, quantity) tuples
            
        Returns:
            List of pricing dictionaries
        """
        pricing_results = []
        
        for product, quantity in product_quantities:
            pricing = PricingService.get_retailer_price(retailer, product, quantity)
            pricing_results.append(pricing)
            
        return pricing_results
    
    @staticmethod
    def create_retailer_pricing(retailer: Retailer, pricing_tier: PricingTier, 
                               product: Optional[Product] = None,
                               custom_discount: Optional[float] = None,
                               custom_price: Optional[float] = None) -> RetailerPricing:
        """
        Create or update retailer pricing assignment.
        
        Args:
            retailer: Retailer instance
            pricing_tier: PricingTier instance
            product: Optional product for specific pricing
            custom_discount: Custom discount percentage
            custom_price: Custom fixed price
            
        Returns:
            RetailerPricing instance
        """
        retailer_pricing, created = RetailerPricing.objects.get_or_create(
            retailer=retailer,
            product=product,
            defaults={
                'pricing_tier': pricing_tier,
                'custom_discount_percentage': custom_discount,
                'custom_price': custom_price
            }
        )
        
        if not created:
            retailer_pricing.pricing_tier = pricing_tier
            retailer_pricing.custom_discount_percentage = custom_discount
            retailer_pricing.custom_price = custom_price
            retailer_pricing.save()
            
        return retailer_pricing
    
    @staticmethod
    def get_pricing_summary(retailer: Retailer) -> Dict:
        """
        Get pricing summary for a retailer.
        
        Args:
            retailer: Retailer instance
            
        Returns:
            Dictionary with pricing summary
        """
        # Get all pricing assignments for this retailer
        pricing_assignments = RetailerPricing.objects.filter(
            retailer=retailer,
            is_active=True
        ).select_related('pricing_tier', 'product')
        
        # Get applicable dynamic pricing rules
        dynamic_rules = DynamicPricing.objects.filter(
            is_active=True
        ).filter(
            models.Q(retailer__isnull=True) | models.Q(retailer=retailer)
        )
        
        return {
            'retailer': retailer.retailer_name,
            'total_pricing_assignments': pricing_assignments.count(),
            'general_tier_assignments': pricing_assignments.filter(product__isnull=True).count(),
            'product_specific_assignments': pricing_assignments.filter(product__isnull=False).count(),
            'applicable_dynamic_rules': dynamic_rules.count(),
            'pricing_assignments': [
                {
                    'tier': assignment.pricing_tier.tier_name,
                    'product': assignment.product.product_name if assignment.product else 'All Products',
                    'custom_discount': assignment.custom_discount_percentage,
                    'custom_price': assignment.custom_price,
                    'effective_from': assignment.effective_from
                }
                for assignment in pricing_assignments
            ]
        }
    
    @staticmethod
    def get_expiry_discounts(days_ahead: int = 7) -> List[Dict]:
        """
        Get suggested expiry discounts for batches nearing expiry.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of expiry discount suggestions
        """
        from inventory.services import InventoryService
        
        expiring_batches = InventoryService.get_expiring_batches(days_ahead)
        discount_suggestions = []
        
        for batch in expiring_batches:
            days_until_expiry = batch.days_until_expiry()
            
            # Suggest discount percentage based on days until expiry
            if days_until_expiry <= 1:
                suggested_discount = 30  # 30% discount for items expiring within 1 day
            elif days_until_expiry <= 3:
                suggested_discount = 20  # 20% discount for items expiring within 3 days
            elif days_until_expiry <= 7:
                suggested_discount = 10  # 10% discount for items expiring within 7 days
            else:
                suggested_discount = 5   # 5% discount for other items
                
            discount_suggestions.append({
                'batch': batch,
                'product': batch.product,
                'days_until_expiry': days_until_expiry,
                'current_quantity': batch.current_quantity,
                'suggested_discount_percentage': suggested_discount,
                'original_price': batch.product.mrp,
                'suggested_price': batch.product.mrp * (1 - suggested_discount/100)
            })
            
        return discount_suggestions
    
    @staticmethod
    def apply_bulk_expiry_discount(batch_ids: List[str], discount_percentage: float) -> Dict:
        """
        Apply expiry discount to multiple batches.
        
        Args:
            batch_ids: List of batch IDs
            discount_percentage: Discount percentage to apply
            
        Returns:
            Dictionary with application results
        """
        applied_count = 0
        failed_count = 0
        failed_batches = []
        
        for batch_id in batch_ids:
            try:
                batch = Batch.objects.get(batch_id=batch_id)
                
                # Create or update dynamic pricing rule for this batch
                rule_name = f"Expiry Discount - {batch.product.product_name} - {batch.manufacturer_batch_number}"
                
                dynamic_rule, created = DynamicPricing.objects.get_or_create(
                    rule_name=rule_name,
                    product=batch.product,
                    defaults={
                        'apply_to_expiring_batches': True,
                        'expiry_threshold_days': batch.days_until_expiry() + 1,
                        'expiry_discount_percentage': discount_percentage,
                        'is_active': True,
                        'priority': 100  # High priority for expiry discounts
                    }
                )
                
                if not created:
                    dynamic_rule.expiry_discount_percentage = discount_percentage
                    dynamic_rule.expiry_threshold_days = batch.days_until_expiry() + 1
                    dynamic_rule.is_active = True
                    dynamic_rule.save()
                    
                applied_count += 1
                
            except Batch.DoesNotExist:
                failed_count += 1
                failed_batches.append(batch_id)
            except Exception as e:
                failed_count += 1
                failed_batches.append(batch_id)
                logger.error(f"Error applying discount to batch {batch_id}: {str(e)}")
                
        return {
            'applied_count': applied_count,
            'failed_count': failed_count,
            'failed_batches': failed_batches,
            'discount_percentage': discount_percentage
        }