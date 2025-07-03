#!/usr/bin/env python3
"""Initialize database with sample data for development."""

from backend import create_app
from backend.models import db, Product, Batch, Retailer, PricingTier, Inventory, Order, OrderItem, Alert, User
from datetime import datetime, date, timedelta
from decimal import Decimal
import os

def init_database():
    """Initialize the database with sample data."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Add sample pricing tiers
        if not PricingTier.query.first():
            tiers = [
                PricingTier(
                    tier_name="Strategic Partners",
                    min_discount_percentage=Decimal('25.00'),
                    max_discount_percentage=Decimal('30.00'),
                    description="High volume, long-term contracts, exclusive agreements"
                ),
                PricingTier(
                    tier_name="Key Accounts",
                    min_discount_percentage=Decimal('20.00'),
                    max_discount_percentage=Decimal('25.00'),
                    description="Consistent medium-to-high volume, established relationship"
                ),
                PricingTier(
                    tier_name="Emerging Accounts",
                    min_discount_percentage=Decimal('15.00'),
                    max_discount_percentage=Decimal('20.00'),
                    description="New customers, lower volume, potential for growth"
                ),
                PricingTier(
                    tier_name="Spot/Ad-hoc",
                    min_discount_percentage=Decimal('10.00'),
                    max_discount_percentage=Decimal('20.00'),
                    description="Urgent, non-contractual orders, specific batch clearance"
                )
            ]
            
            for tier in tiers:
                db.session.add(tier)
            db.session.commit()
            print("Added pricing tiers")
        
        # Add sample products
        if not Product.query.first():
            products = [
                Product(
                    sku="ARV-001",
                    product_name="Organic Basmati Rice",
                    category="Grains",
                    brand="Arivu Organic",
                    mrp=Decimal('150.00'),
                    weight_per_unit=Decimal('1.000'),
                    unit_of_measure="kg",
                    shelf_life_days=365,
                    storage_requirements="Cool, dry place",
                    is_perishable=True,
                    description="Premium organic basmati rice"
                ),
                Product(
                    sku="ARV-002",
                    product_name="Fresh Tomatoes",
                    category="Vegetables",
                    brand="Arivu Fresh",
                    mrp=Decimal('80.00'),
                    weight_per_unit=Decimal('1.000'),
                    unit_of_measure="kg",
                    shelf_life_days=7,
                    storage_requirements="Refrigerated storage",
                    is_perishable=True,
                    description="Fresh red tomatoes"
                ),
                Product(
                    sku="ARV-003",
                    product_name="Wheat Flour",
                    category="Grains",
                    brand="Arivu Mills",
                    mrp=Decimal('45.00'),
                    weight_per_unit=Decimal('1.000'),
                    unit_of_measure="kg",
                    shelf_life_days=180,
                    storage_requirements="Dry storage",
                    is_perishable=True,
                    description="All-purpose wheat flour"
                ),
                Product(
                    sku="ARV-004",
                    product_name="Organic Milk",
                    category="Dairy",
                    brand="Arivu Dairy",
                    mrp=Decimal('60.00'),
                    weight_per_unit=Decimal('1.000'),
                    unit_of_measure="liter",
                    shelf_life_days=5,
                    storage_requirements="Refrigerated below 4°C",
                    is_perishable=True,
                    description="Fresh organic milk"
                ),
                Product(
                    sku="ARV-005",
                    product_name="Mixed Spices",
                    category="Spices",
                    brand="Arivu Spices",
                    mrp=Decimal('120.00'),
                    weight_per_unit=Decimal('0.250'),
                    unit_of_measure="kg",
                    shelf_life_days=730,
                    storage_requirements="Dry, cool place",
                    is_perishable=False,
                    description="Blend of traditional spices"
                )
            ]
            
            for product in products:
                db.session.add(product)
            db.session.commit()
            print("Added products")
        
        # Add sample retailers
        if not Retailer.query.first():
            retailers = [
                Retailer(
                    retailer_name="Metro Supermart",
                    contact_person="John Smith",
                    email="john@metrosupermart.com",
                    phone_number="+1-555-0101",
                    address="123 Main St",
                    city="New York",
                    state="NY",
                    zip_code="10001",
                    pricing_tier_id=1,  # Strategic Partners
                    account_status="Active"
                ),
                Retailer(
                    retailer_name="Fresh Foods Co.",
                    contact_person="Sarah Johnson",
                    email="sarah@freshfoods.com",
                    phone_number="+1-555-0102",
                    address="456 Oak Ave",
                    city="Los Angeles",
                    state="CA",
                    zip_code="90001",
                    pricing_tier_id=2,  # Key Accounts
                    account_status="Active"
                ),
                Retailer(
                    retailer_name="Corner Store",
                    contact_person="Mike Wilson",
                    email="mike@cornerstore.com",
                    phone_number="+1-555-0103",
                    address="789 Pine St",
                    city="Chicago",
                    state="IL",
                    zip_code="60601",
                    pricing_tier_id=3,  # Emerging Accounts
                    account_status="Active"
                )
            ]
            
            for retailer in retailers:
                db.session.add(retailer)
            db.session.commit()
            print("Added retailers")
        
        # Add sample batches
        if not Batch.query.first():
            products = Product.query.all()
            batches = [
                Batch(
                    product_id=products[0].product_id,  # Basmati Rice
                    manufacturer_batch_number="BR-2024-001",
                    production_date=date.today() - timedelta(days=30),
                    expiration_date=date.today() + timedelta(days=300),
                    initial_quantity=Decimal('500.00'),
                    current_quantity=Decimal('350.00'),
                    status="In Stock",
                    manufacturing_location="Punjab, India"
                ),
                Batch(
                    product_id=products[1].product_id,  # Tomatoes
                    manufacturer_batch_number="TM-2024-001",
                    production_date=date.today() - timedelta(days=2),
                    expiration_date=date.today() + timedelta(days=5),
                    initial_quantity=Decimal('200.00'),
                    current_quantity=Decimal('150.00'),
                    status="In Stock",
                    manufacturing_location="California, USA"
                ),
                Batch(
                    product_id=products[2].product_id,  # Wheat Flour
                    manufacturer_batch_number="WF-2024-001",
                    production_date=date.today() - timedelta(days=45),
                    expiration_date=date.today() + timedelta(days=120),
                    initial_quantity=Decimal('1000.00'),
                    current_quantity=Decimal('800.00'),
                    status="In Stock",
                    manufacturing_location="Kansas, USA"
                ),
                Batch(
                    product_id=products[3].product_id,  # Milk
                    manufacturer_batch_number="ML-2024-001",
                    production_date=date.today() - timedelta(days=1),
                    expiration_date=date.today() + timedelta(days=3),
                    initial_quantity=Decimal('300.00'),
                    current_quantity=Decimal('200.00'),
                    status="In Stock",
                    manufacturing_location="Vermont, USA"
                )
            ]
            
            for batch in batches:
                db.session.add(batch)
            db.session.commit()
            print("Added batches")
        
        # Add sample inventory
        if not Inventory.query.first():
            batches = Batch.query.all()
            inventory_items = [
                Inventory(
                    batch_id=batches[0].batch_id,
                    location="Warehouse A",
                    quantity_on_hand=Decimal('350.00'),
                    reorder_point=Decimal('100.00')
                ),
                Inventory(
                    batch_id=batches[1].batch_id,
                    location="Cold Storage 1",
                    quantity_on_hand=Decimal('150.00'),
                    reorder_point=Decimal('50.00')
                ),
                Inventory(
                    batch_id=batches[2].batch_id,
                    location="Warehouse B",
                    quantity_on_hand=Decimal('800.00'),
                    reorder_point=Decimal('200.00')
                ),
                Inventory(
                    batch_id=batches[3].batch_id,
                    location="Cold Storage 2",
                    quantity_on_hand=Decimal('200.00'),
                    reorder_point=Decimal('100.00')
                )
            ]
            
            for inventory in inventory_items:
                db.session.add(inventory)
            db.session.commit()
            print("Added inventory")
        
        # Add sample user
        if not User.query.first():
            user = User(
                username="admin",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewfBmdJ9CpHUxVG2",  # password: admin
                email="admin@arivufoods.com",
                first_name="Admin",
                last_name="User",
                role="Admin"
            )
            db.session.add(user)
            db.session.commit()
            print("Added admin user")
        
        print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()