"""
FIFO/FEFO inventory management services for Arivu Foods SCMS.
"""

from django.db import transaction
from django.db import models
from django.utils import timezone
from .models import Product, Batch, Inventory
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class InventoryService:
    """Service class for managing inventory with FIFO/FEFO logic."""
    
    @staticmethod
    def get_available_batches_fifo(product: Product, location: str = None) -> List[Batch]:
        """
        Get available batches for a product ordered by FIFO (First In, First Out).
        
        Args:
            product: Product instance
            location: Optional location filter
            
        Returns:
            List of available batches ordered by production date (oldest first)
        """
        queryset = Batch.objects.filter(
            product=product,
            current_quantity__gt=0,
            status='in_stock'
        ).order_by('production_date')
        
        if location:
            queryset = queryset.filter(
                inventory_records__location=location,
                inventory_records__quantity_on_hand__gt=0
            )
            
        return list(queryset)
    
    @staticmethod
    def get_available_batches_fefo(product: Product, location: str = None) -> List[Batch]:
        """
        Get available batches for a product ordered by FEFO (First Expiry, First Out).
        
        Args:
            product: Product instance
            location: Optional location filter
            
        Returns:
            List of available batches ordered by expiry date (earliest expiry first)
        """
        queryset = Batch.objects.filter(
            product=product,
            current_quantity__gt=0,
            status='in_stock',
            expiration_date__gt=timezone.now().date()
        ).order_by('expiration_date')
        
        if location:
            queryset = queryset.filter(
                inventory_records__location=location,
                inventory_records__quantity_on_hand__gt=0
            )
            
        return list(queryset)
    
    @staticmethod
    def get_expiring_batches(days_ahead: int = 7) -> List[Batch]:
        """
        Get batches that will expire within specified days.
        
        Args:
            days_ahead: Number of days to look ahead for expiry
            
        Returns:
            List of batches expiring within specified days
        """
        expiry_threshold = timezone.now().date() + timezone.timedelta(days=days_ahead)
        
        return Batch.objects.filter(
            expiration_date__lte=expiry_threshold,
            expiration_date__gt=timezone.now().date(),
            current_quantity__gt=0,
            status='in_stock'
        ).order_by('expiration_date')
    
    @staticmethod
    def allocate_inventory_fifo(product: Product, requested_quantity: float, 
                               location: str = None) -> List[Tuple[Batch, float]]:
        """
        Allocate inventory using FIFO logic.
        
        Args:
            product: Product to allocate
            requested_quantity: Quantity needed
            location: Optional location constraint
            
        Returns:
            List of (batch, allocated_quantity) tuples
        """
        allocations = []
        remaining_quantity = requested_quantity
        
        available_batches = InventoryService.get_available_batches_fifo(product, location)
        
        for batch in available_batches:
            if remaining_quantity <= 0:
                break
                
            available_in_batch = batch.current_quantity
            allocation_quantity = min(remaining_quantity, available_in_batch)
            
            allocations.append((batch, allocation_quantity))
            remaining_quantity -= allocation_quantity
            
        return allocations
    
    @staticmethod
    def allocate_inventory_fefo(product: Product, requested_quantity: float,
                               location: str = None) -> List[Tuple[Batch, float]]:
        """
        Allocate inventory using FEFO logic.
        
        Args:
            product: Product to allocate
            requested_quantity: Quantity needed
            location: Optional location constraint
            
        Returns:
            List of (batch, allocated_quantity) tuples
        """
        allocations = []
        remaining_quantity = requested_quantity
        
        available_batches = InventoryService.get_available_batches_fefo(product, location)
        
        for batch in available_batches:
            if remaining_quantity <= 0:
                break
                
            available_in_batch = batch.current_quantity
            allocation_quantity = min(remaining_quantity, available_in_batch)
            
            allocations.append((batch, allocation_quantity))
            remaining_quantity -= allocation_quantity
            
        return allocations
    
    @staticmethod
    @transaction.atomic
    def fulfill_order_item(product: Product, requested_quantity: float,
                          location: str = None, method: str = 'fefo') -> dict:
        """
        Fulfill an order item using specified allocation method.
        
        Args:
            product: Product to fulfill
            requested_quantity: Quantity needed
            location: Optional location constraint
            method: Allocation method ('fifo' or 'fefo')
            
        Returns:
            Dictionary with fulfillment details
        """
        if method.lower() == 'fifo':
            allocations = InventoryService.allocate_inventory_fifo(
                product, requested_quantity, location
            )
        else:  # Default to FEFO for perishable goods
            allocations = InventoryService.allocate_inventory_fefo(
                product, requested_quantity, location
            )
        
        total_allocated = sum(allocation[1] for allocation in allocations)
        
        if total_allocated < requested_quantity:
            return {
                'success': False,
                'allocated_quantity': total_allocated,
                'shortage': requested_quantity - total_allocated,
                'allocations': allocations,
                'message': f'Insufficient inventory. Only {total_allocated} available.'
            }
        
        # Actually allocate the quantities
        for batch, allocation_quantity in allocations:
            batch.allocate_quantity(allocation_quantity)
            
        return {
            'success': True,
            'allocated_quantity': total_allocated,
            'shortage': 0,
            'allocations': allocations,
            'message': 'Order fulfilled successfully.'
        }
    
    @staticmethod
    def get_low_stock_alerts(location: str = None) -> List[dict]:
        """
        Get low stock alerts for all inventory items.
        
        Args:
            location: Optional location filter
            
        Returns:
            List of low stock alert dictionaries
        """
        alerts = []
        
        inventory_queryset = Inventory.objects.filter(
            reorder_point__isnull=False,
            quantity_on_hand__lte=models.F('reorder_point')
        )
        
        if location:
            inventory_queryset = inventory_queryset.filter(location=location)
            
        for inventory in inventory_queryset:
            alerts.append({
                'product': inventory.batch.product,
                'batch': inventory.batch,
                'location': inventory.location,
                'current_quantity': inventory.quantity_on_hand,
                'reorder_point': inventory.reorder_point,
                'deficit': inventory.reorder_point - inventory.quantity_on_hand,
                'alert_type': 'low_stock'
            })
            
        return alerts
    
    @staticmethod
    def get_expiry_alerts(days_ahead: int = 7) -> List[dict]:
        """
        Get expiry alerts for batches expiring soon.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of expiry alert dictionaries
        """
        alerts = []
        expiring_batches = InventoryService.get_expiring_batches(days_ahead)
        
        for batch in expiring_batches:
            alerts.append({
                'product': batch.product,
                'batch': batch,
                'expiration_date': batch.expiration_date,
                'days_until_expiry': batch.days_until_expiry(),
                'current_quantity': batch.current_quantity,
                'alert_type': 'expiry_warning'
            })
            
        return alerts
    
    @staticmethod
    def get_inventory_summary(location: str = None) -> dict:
        """
        Get inventory summary with key metrics.
        
        Args:
            location: Optional location filter
            
        Returns:
            Dictionary with inventory summary
        """
        inventory_queryset = Inventory.objects.all()
        
        if location:
            inventory_queryset = inventory_queryset.filter(location=location)
            
        total_items = inventory_queryset.count()
        total_value = sum(
            inv.quantity_on_hand * inv.batch.product.mrp 
            for inv in inventory_queryset
        )
        
        low_stock_count = len(InventoryService.get_low_stock_alerts(location))
        expiry_alerts_count = len(InventoryService.get_expiry_alerts())
        
        return {
            'total_items': total_items,
            'total_value': total_value,
            'low_stock_alerts': low_stock_count,
            'expiry_alerts': expiry_alerts_count,
            'location': location or 'All Locations'
        }