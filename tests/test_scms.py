"""Basic tests for the Arivu Foods SCMS."""

import unittest
import json
from datetime import datetime, date, timedelta
from decimal import Decimal

from backend import create_app
from backend.models import db, Product, Batch, Retailer, PricingTier, Inventory


class SCMSTestCase(unittest.TestCase):
    """Test case for SCMS functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            self._create_test_data()
    
    def tearDown(self):
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_data(self):
        """Create test data."""
        # Create pricing tier
        tier = PricingTier(
            tier_name="Test Tier",
            min_discount_percentage=Decimal('20.00'),
            max_discount_percentage=Decimal('25.00'),
            description="Test pricing tier"
        )
        db.session.add(tier)
        
        # Create product
        product = Product(
            sku="TEST-001",
            product_name="Test Product",
            category="Test",
            brand="Test Brand",
            mrp=Decimal('100.00'),
            shelf_life_days=30,
            is_perishable=True
        )
        db.session.add(product)
        
        # Create retailer
        retailer = Retailer(
            retailer_name="Test Retailer",
            email="test@retailer.com",
            pricing_tier_id=1,
            account_status="Active"
        )
        db.session.add(retailer)
        
        # Create batch
        batch = Batch(
            product_id=1,
            manufacturer_batch_number="BATCH-001",
            production_date=date.today() - timedelta(days=5),
            expiration_date=date.today() + timedelta(days=5),  # Within 7-day threshold
            initial_quantity=Decimal('100.00'),
            current_quantity=Decimal('80.00'),
            status="In Stock"
        )
        db.session.add(batch)
        
        # Create inventory
        inventory = Inventory(
            batch_id=1,
            location="Test Warehouse",
            quantity_on_hand=Decimal('80.00'),
            reorder_point=Decimal('20.00')
        )
        db.session.add(inventory)
        
        db.session.commit()
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
    
    def test_get_products(self):
        """Test getting products."""
        response = self.client.get('/api/products')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['sku'], 'TEST-001')
        self.assertEqual(data[0]['product_name'], 'Test Product')
    
    def test_get_batches_fefo_order(self):
        """Test getting batches with FEFO ordering."""
        response = self.client.get('/api/batches?order_by=expiration_date')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['manufacturer_batch_number'], 'BATCH-001')
        self.assertEqual(data[0]['days_until_expiry'], 5)
    
    def test_dynamic_pricing(self):
        """Test dynamic pricing calculation."""
        pricing_data = {
            'product_id': 1,
            'retailer_id': 1,
            'quantity': 5
        }
        
        response = self.client.post('/api/pricing/calculate',
                                   data=json.dumps(pricing_data),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should get middle of discount range (22.5%)
        self.assertEqual(data['base_price'], 100.0)
        self.assertEqual(data['discount_percentage'], 22.5)
        self.assertEqual(data['final_price'], 77.5)
        self.assertEqual(data['total_amount'], 387.5)
    
    def test_inventory_tracking(self):
        """Test inventory tracking."""
        response = self.client.get('/api/inventory')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        
        inventory = data[0]
        self.assertEqual(inventory['product_name'], 'Test Product')
        self.assertEqual(inventory['quantity_on_hand'], 80.0)
        self.assertEqual(inventory['reorder_point'], 20.0)
        self.assertFalse(inventory['is_low_stock'])
    
    def test_expiration_alerts(self):
        """Test expiration alert generation."""
        response = self.client.post('/api/alerts/check-expiration')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should create 1 alert for batch expiring in 10 days (within 7-day threshold)
        self.assertEqual(data['alerts_created'], 1)
        
        # Check alerts endpoint
        response = self.client.get('/api/alerts')
        self.assertEqual(response.status_code, 200)
        alerts = json.loads(response.data)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['alert_type'], 'Expiration')
    
    def test_dashboard_summary(self):
        """Test dashboard summary."""
        response = self.client.get('/api/dashboard/summary')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check counts
        self.assertEqual(data['counts']['total_products'], 1)
        self.assertEqual(data['counts']['total_batches'], 1)
        self.assertEqual(data['counts']['active_retailers'], 1)
        self.assertEqual(data['counts']['pending_orders'], 0)
        
        # Check expiring soon
        self.assertEqual(len(data['expiring_soon']), 1)
        self.assertEqual(data['expiring_soon'][0]['days_until_expiry'], 5)
    
    def test_weather_api(self):
        """Test weather API with fallback."""
        response = self.client.get('/api/weather')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should return mock data when API key not configured
        self.assertIn('mock_data', data)
        self.assertEqual(data['mock_data']['temperature'], 22.5)
    
    def test_create_product(self):
        """Test creating a new product."""
        product_data = {
            'sku': 'NEW-001',
            'product_name': 'New Product',
            'category': 'New Category',
            'brand': 'New Brand',
            'mrp': 150.00,
            'shelf_life_days': 60,
            'is_perishable': True
        }
        
        response = self.client.post('/api/products',
                                   data=json.dumps(product_data),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('product_id', data)
        self.assertEqual(data['message'], 'Product created successfully')
    
    def test_create_batch(self):
        """Test creating a new batch."""
        batch_data = {
            'product_id': 1,
            'manufacturer_batch_number': 'NEW-BATCH-001',
            'production_date': '2025-07-01',
            'expiration_date': '2025-08-01',
            'initial_quantity': 200.00
        }
        
        response = self.client.post('/api/batches',
                                   data=json.dumps(batch_data),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('batch_id', data)
        self.assertEqual(data['message'], 'Batch created successfully')


if __name__ == '__main__':
    unittest.main()