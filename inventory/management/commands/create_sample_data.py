"""
Django management command to create sample data for Arivu Foods SCMS.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from inventory.models import Product, Batch, Inventory
from pricing.models import Retailer, PricingTier, RetailerPricing
from alerts.services import AlertService


class Command(BaseCommand):
    help = 'Create sample data for Arivu Foods SCMS'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data for Arivu Foods SCMS...')
        
        # Create sample products
        self.create_products()
        
        # Create sample retailers and pricing tiers
        self.create_retailers_and_pricing()
        
        # Create sample batches
        self.create_batches()
        
        # Create sample inventory
        self.create_inventory()
        
        # Run alert checks
        self.create_alerts()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
    
    def create_products(self):
        """Create sample products."""
        products_data = [
            {
                'sku': 'AF-MP-001',
                'product_name': 'Organic Mango Pulp',
                'description': 'Premium organic mango pulp from Alphonso mangoes',
                'category': 'Fruit Pulp',
                'brand': 'Arivu Organics',
                'mrp': Decimal('45.00'),
                'weight_per_unit': Decimal('1.000'),
                'unit_of_measure': 'kg',
                'shelf_life_days': 365,
                'storage_requirements': 'Cool, dry place',
                'is_perishable': True
            },
            {
                'sku': 'AF-TP-002',
                'product_name': 'Turmeric Powder',
                'description': 'Pure turmeric powder with high curcumin content',
                'category': 'Spices',
                'brand': 'Arivu Spices',
                'mrp': Decimal('120.00'),
                'weight_per_unit': Decimal('0.500'),
                'unit_of_measure': 'kg',
                'shelf_life_days': 730,
                'storage_requirements': 'Dry place, away from light',
                'is_perishable': True
            },
            {
                'sku': 'AF-CP-003',
                'product_name': 'Coriander Powder',
                'description': 'Freshly ground coriander powder',
                'category': 'Spices',
                'brand': 'Arivu Spices',
                'mrp': Decimal('85.00'),
                'weight_per_unit': Decimal('0.250'),
                'unit_of_measure': 'kg',
                'shelf_life_days': 545,
                'storage_requirements': 'Dry place',
                'is_perishable': True
            },
            {
                'sku': 'AF-RP-004',
                'product_name': 'Red Chili Powder',
                'description': 'Hot and flavorful red chili powder',
                'category': 'Spices',
                'brand': 'Arivu Spices',
                'mrp': Decimal('95.00'),
                'weight_per_unit': Decimal('0.250'),
                'unit_of_measure': 'kg',
                'shelf_life_days': 545,
                'storage_requirements': 'Dry place, away from moisture',
                'is_perishable': True
            },
            {
                'sku': 'AF-CO-005',
                'product_name': 'Coconut Oil',
                'description': 'Cold-pressed virgin coconut oil',
                'category': 'Oils',
                'brand': 'Arivu Naturals',
                'mrp': Decimal('280.00'),
                'weight_per_unit': Decimal('1.000'),
                'unit_of_measure': 'liter',
                'shelf_life_days': 730,
                'storage_requirements': 'Cool place, away from direct sunlight',
                'is_perishable': True
            }
        ]
        
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                sku=product_data['sku'],
                defaults=product_data
            )
            if created:
                self.stdout.write(f'Created product: {product.product_name}')
    
    def create_retailers_and_pricing(self):
        """Create sample retailers and pricing tiers."""
        
        # Create pricing tiers
        tiers_data = [
            {
                'tier_name': 'Premium Partners',
                'description': 'High-volume strategic partners with exclusive agreements',
                'discount_percentage': Decimal('25.00'),
                'minimum_order_value': Decimal('50000.00')
            },
            {
                'tier_name': 'Key Accounts',
                'description': 'Medium to high volume consistent customers',
                'discount_percentage': Decimal('20.00'),
                'minimum_order_value': Decimal('25000.00')
            },
            {
                'tier_name': 'Standard Retailers',
                'description': 'Regular retailers with consistent orders',
                'discount_percentage': Decimal('15.00'),
                'minimum_order_value': Decimal('10000.00')
            },
            {
                'tier_name': 'New Partners',
                'description': 'New customers and emerging accounts',
                'discount_percentage': Decimal('10.00'),
                'minimum_order_value': Decimal('5000.00')
            }
        ]
        
        for tier_data in tiers_data:
            tier, created = PricingTier.objects.get_or_create(
                tier_name=tier_data['tier_name'],
                defaults=tier_data
            )
            if created:
                self.stdout.write(f'Created pricing tier: {tier.tier_name}')
        
        # Create retailers
        retailers_data = [
            {
                'retailer_name': 'Mumbai Spice Market',
                'contact_person': 'Rajesh Kumar',
                'email': 'rajesh@mumbaiSpicemarket.com',
                'phone': '+91-98765-43210',
                'address': '123 Crawford Market, Mumbai',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'tier': 'Premium Partners'
            },
            {
                'retailer_name': 'Delhi Organic Store',
                'contact_person': 'Priya Sharma',
                'email': 'priya@delhiorganic.com',
                'phone': '+91-98765-43211',
                'address': '456 Connaught Place, New Delhi',
                'city': 'New Delhi',
                'state': 'Delhi',
                'tier': 'Key Accounts'
            },
            {
                'retailer_name': 'Bangalore Fresh Foods',
                'contact_person': 'Suresh Reddy',
                'email': 'suresh@bangalorefresh.com',
                'phone': '+91-98765-43212',
                'address': '789 Commercial Street, Bangalore',
                'city': 'Bangalore',
                'state': 'Karnataka',
                'tier': 'Standard Retailers'
            },
            {
                'retailer_name': 'Chennai Natural Products',
                'contact_person': 'Lakshmi Nair',
                'email': 'lakshmi@chennainatural.com',
                'phone': '+91-98765-43213',
                'address': '321 T. Nagar, Chennai',
                'city': 'Chennai',
                'state': 'Tamil Nadu',
                'tier': 'Key Accounts'
            },
            {
                'retailer_name': 'Hyderabad Spice Corner',
                'contact_person': 'Ahmed Khan',
                'email': 'ahmed@hyderabadspice.com',
                'phone': '+91-98765-43214',
                'address': '654 Sultan Bazar, Hyderabad',
                'city': 'Hyderabad',
                'state': 'Telangana',
                'tier': 'New Partners'
            }
        ]
        
        for retailer_data in retailers_data:
            tier_name = retailer_data.pop('tier')
            tier = PricingTier.objects.get(tier_name=tier_name)
            
            retailer, created = Retailer.objects.get_or_create(
                retailer_name=retailer_data['retailer_name'],
                defaults=retailer_data
            )
            
            if created:
                self.stdout.write(f'Created retailer: {retailer.retailer_name}')
                
                # Create retailer pricing assignment
                RetailerPricing.objects.get_or_create(
                    retailer=retailer,
                    pricing_tier=tier,
                    product=None  # General tier assignment
                )
    
    def create_batches(self):
        """Create sample batches."""
        products = Product.objects.all()
        
        for product in products:
            # Create 3-5 batches per product
            for i in range(3):
                production_date = date.today() - timedelta(days=30 + i*15)
                expiration_date = production_date + timedelta(days=product.shelf_life_days)
                
                # Some batches closer to expiry for testing alerts
                if i == 0:
                    production_date = date.today() - timedelta(days=product.shelf_life_days - 10)
                    expiration_date = date.today() + timedelta(days=10)
                
                batch_data = {
                    'product': product,
                    'manufacturer_batch_number': f'MFG-{product.sku}-{production_date.strftime("%Y%m%d")}-{i+1:02d}',
                    'production_date': production_date,
                    'expiration_date': expiration_date,
                    'initial_quantity': Decimal('1000.00') - (i * Decimal('100.00')),
                    'current_quantity': Decimal('800.00') - (i * Decimal('150.00')),
                    'status': 'in_stock',
                    'manufacturing_location': f'Plant {i+1}'
                }
                
                batch, created = Batch.objects.get_or_create(
                    product=product,
                    manufacturer_batch_number=batch_data['manufacturer_batch_number'],
                    defaults=batch_data
                )
                
                if created:
                    self.stdout.write(f'Created batch: {batch.manufacturer_batch_number}')
    
    def create_inventory(self):
        """Create sample inventory records."""
        batches = Batch.objects.all()
        locations = ['Main Warehouse', 'Distribution Center A', 'Distribution Center B']
        
        for batch in batches:
            for location in locations:
                # Not all batches in all locations
                if hash(f"{batch.batch_id}{location}") % 3 == 0:
                    continue
                
                inventory_data = {
                    'batch': batch,
                    'location': location,
                    'quantity_on_hand': batch.current_quantity / len(locations),
                    'reorder_point': Decimal('50.00')
                }
                
                inventory, created = Inventory.objects.get_or_create(
                    batch=batch,
                    location=location,
                    defaults=inventory_data
                )
                
                if created:
                    self.stdout.write(f'Created inventory: {batch.product.product_name} at {location}')
    
    def create_alerts(self):
        """Create sample alerts by running alert checks."""
        self.stdout.write('Running alert checks...')
        
        # Run expiry alerts
        expiry_alerts = AlertService.check_expiry_alerts(days_ahead=30)
        self.stdout.write(f'Created {len(expiry_alerts)} expiry alerts')
        
        # Run low stock alerts
        low_stock_alerts = AlertService.check_low_stock_alerts()
        self.stdout.write(f'Created {len(low_stock_alerts)} low stock alerts')
        
        # Run expired batch alerts
        expired_alerts = AlertService.check_expired_batches()
        self.stdout.write(f'Created {len(expired_alerts)} expired batch alerts')