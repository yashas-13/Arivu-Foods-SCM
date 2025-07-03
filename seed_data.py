"""Seed sample data for the Arivu Foods SCMS."""
from datetime import datetime, date, timedelta
from decimal import Decimal
from backend.models import db, Product, Batch, Retailer, PricingTier, Order, OrderItem, Inventory
from backend import create_app


def seed_pricing_tiers():
    """Create pricing tiers for retailers."""
    tiers = [
        {
            'tier_name': 'Premium Partners',
            'min_discount_percentage': 25.0,
            'max_discount_percentage': 30.0,
            'description': 'Top-tier retailers with highest volume commitments'
        },
        {
            'tier_name': 'Key Accounts',
            'min_discount_percentage': 20.0,
            'max_discount_percentage': 25.0,
            'description': 'Established retailers with consistent orders'
        },
        {
            'tier_name': 'Standard Partners',
            'min_discount_percentage': 15.0,
            'max_discount_percentage': 20.0,
            'description': 'Regular retailers with moderate volumes'
        },
        {
            'tier_name': 'New Accounts',
            'min_discount_percentage': 10.0,
            'max_discount_percentage': 15.0,
            'description': 'New retailers being onboarded'
        }
    ]
    
    for tier_data in tiers:
        tier = PricingTier(**tier_data)
        db.session.add(tier)
    
    db.session.commit()
    print("✅ Pricing tiers seeded")


def seed_products():
    """Create sample products."""
    products = [
        {
            'sku': 'ARV-SNK-001',
            'product_name': 'Arivu Organic Banana Chips',
            'description': 'Crispy organic banana chips made from premium Kerala bananas',
            'category': 'Snacks',
            'brand': 'Arivu Foods',
            'mrp': Decimal('150.00'),
            'weight_per_unit': Decimal('200.000'),
            'unit_of_measure': 'grams',
            'shelf_life_days': 180,
            'storage_requirements': 'Cool, dry place',
            'is_perishable': True
        },
        {
            'sku': 'ARV-SNK-002',
            'product_name': 'Arivu Spiced Cashews',
            'description': 'Premium roasted cashews with traditional Indian spices',
            'category': 'Snacks',
            'brand': 'Arivu Foods',
            'mrp': Decimal('320.00'),
            'weight_per_unit': Decimal('250.000'),
            'unit_of_measure': 'grams',
            'shelf_life_days': 365,
            'storage_requirements': 'Cool, dry place',
            'is_perishable': True
        },
        {
            'sku': 'ARV-BEV-001',
            'product_name': 'Arivu Tender Coconut Water',
            'description': 'Fresh tender coconut water with natural electrolytes',
            'category': 'Beverages',
            'brand': 'Arivu Foods',
            'mrp': Decimal('65.00'),
            'weight_per_unit': Decimal('250.000'),
            'unit_of_measure': 'ml',
            'shelf_life_days': 90,
            'storage_requirements': 'Refrigerate after opening',
            'is_perishable': True
        },
        {
            'sku': 'ARV-DAI-001',
            'product_name': 'Arivu A2 Ghee',
            'description': 'Pure A2 cow ghee made using traditional bilona method',
            'category': 'Dairy',
            'brand': 'Arivu Foods',
            'mrp': Decimal('850.00'),
            'weight_per_unit': Decimal('500.000'),
            'unit_of_measure': 'ml',
            'shelf_life_days': 730,
            'storage_requirements': 'Cool, dry place',
            'is_perishable': True
        },
        {
            'sku': 'ARV-BAK-001',
            'product_name': 'Arivu Multigrain Bread',
            'description': 'Healthy multigrain bread with no preservatives',
            'category': 'Bakery',
            'brand': 'Arivu Foods',
            'mrp': Decimal('55.00'),
            'weight_per_unit': Decimal('400.000'),
            'unit_of_measure': 'grams',
            'shelf_life_days': 5,
            'storage_requirements': 'Room temperature',
            'is_perishable': True
        }
    ]
    
    for product_data in products:
        product = Product(**product_data)
        db.session.add(product)
    
    db.session.commit()
    print("✅ Products seeded")


def seed_retailers():
    """Create sample retailers."""
    retailers = [
        {
            'retailer_name': 'Mumbai Organic Store',
            'contact_person': 'Raj Patel',
            'email': 'raj@mumbaiorganicstore.com',
            'phone_number': '+91 98765 43210',
            'address': '123 Link Road, Bandra West',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'zip_code': '400050',
            'pricing_tier_id': 1,  # Premium Partners
            'account_status': 'Active'
        },
        {
            'retailer_name': 'Delhi Health Foods',
            'contact_person': 'Priya Sharma',
            'email': 'priya@delhihealthfoods.com',
            'phone_number': '+91 98765 43211',
            'address': '456 Connaught Place',
            'city': 'New Delhi',
            'state': 'Delhi',
            'zip_code': '110001',
            'pricing_tier_id': 2,  # Key Accounts
            'account_status': 'Active'
        },
        {
            'retailer_name': 'Bangalore Natural Market',
            'contact_person': 'Arjun Kumar',
            'email': 'arjun@bangalorenatural.com',
            'phone_number': '+91 98765 43212',
            'address': '789 Brigade Road',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'zip_code': '560025',
            'pricing_tier_id': 2,  # Key Accounts
            'account_status': 'Active'
        },
        {
            'retailer_name': 'Chennai Fresh Mart',
            'contact_person': 'Deepika Iyer',
            'email': 'deepika@chennaifresh.com',
            'phone_number': '+91 98765 43213',
            'address': '321 T. Nagar',
            'city': 'Chennai',
            'state': 'Tamil Nadu',
            'zip_code': '600017',
            'pricing_tier_id': 3,  # Standard Partners
            'account_status': 'Active'
        },
        {
            'retailer_name': 'Kolkata Organic Hub',
            'contact_person': 'Sanjay Banerjee',
            'email': 'sanjay@kolkataorganic.com',
            'phone_number': '+91 98765 43214',
            'address': '654 Park Street',
            'city': 'Kolkata',
            'state': 'West Bengal',
            'zip_code': '700016',
            'pricing_tier_id': 4,  # New Accounts
            'account_status': 'Active'
        }
    ]
    
    for retailer_data in retailers:
        retailer = Retailer(**retailer_data)
        db.session.add(retailer)
    
    db.session.commit()
    print("✅ Retailers seeded")


def seed_batches():
    """Create sample batches for products."""
    products = Product.query.all()
    
    for product in products:
        # Create 2-3 batches per product with different expiration dates
        for i in range(3):
            production_date = date.today() - timedelta(days=30 + i*10)
            expiration_date = production_date + timedelta(days=product.shelf_life_days)
            
            batch = Batch(
                product_id=product.product_id,
                manufacturer_batch_number=f'MFG-{product.sku[-3:]}-{i+1:03d}',
                production_date=production_date,
                expiration_date=expiration_date,
                initial_quantity=Decimal(str(100 + i*50)),  # Varying quantities
                current_quantity=Decimal(str(80 + i*40)),   # Some quantities used
                status='In Stock',
                manufacturing_location='Arivu Foods Factory, Kerala'
            )
            db.session.add(batch)
            
            # Create inventory record for each batch
            inventory = Inventory(
                batch_id=batch.batch_id,
                location='Main Warehouse',
                quantity_on_hand=batch.current_quantity,
                reorder_point=Decimal('20.0')
            )
            
            # Need to flush to get batch_id for inventory
            db.session.flush()
            inventory.batch_id = batch.batch_id
            db.session.add(inventory)
    
    db.session.commit()
    print("✅ Batches and inventory seeded")


def seed_orders():
    """Create sample orders."""
    retailers = Retailer.query.all()
    products = Product.query.all()
    
    for i, retailer in enumerate(retailers):
        # Create 1-2 orders per retailer
        for j in range(2):
            order_date = datetime.utcnow() - timedelta(days=j*15 + i*5)
            
            order = Order(
                retailer_id=retailer.retailer_id,
                order_date=order_date,
                total_amount=Decimal('0.00'),  # Will calculate after adding items
                order_status='Delivered' if j == 1 else 'Processing',
                delivery_address=retailer.address,
                expected_delivery_date=order_date.date() + timedelta(days=3)
            )
            db.session.add(order)
            db.session.flush()  # Get order_id
            
            # Add 2-3 products to each order
            total_amount = Decimal('0.00')
            for k in range(2):
                product = products[k % len(products)]
                quantity = Decimal(str(5 + k*2))
                
                # Calculate pricing based on retailer tier
                discount_percentage = Decimal('20.0')  # Default discount
                if retailer.pricing_tier:
                    discount_percentage = retailer.pricing_tier.min_discount_percentage
                
                unit_price = product.mrp * (Decimal('100') - discount_percentage) / Decimal('100')
                line_total = unit_price * quantity
                
                order_item = OrderItem(
                    order_id=order.order_id,
                    product_id=product.product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=line_total,
                    discount_percentage=discount_percentage,
                    actual_sales_price=unit_price
                )
                db.session.add(order_item)
                total_amount += line_total
            
            order.total_amount = total_amount
    
    db.session.commit()
    print("✅ Orders seeded")


def main():
    """Main function to seed all data."""
    app = create_app()
    
    with app.app_context():
        print("🌱 Starting data seeding...")
        
        # Clear existing data (optional - be careful in production!)
        print("🗑️  Clearing existing data...")
        db.drop_all()
        db.create_all()
        
        # Seed data in correct order
        seed_pricing_tiers()
        seed_products()
        seed_retailers()
        seed_batches()
        seed_orders()
        
        print("🎉 Data seeding completed successfully!")
        print(f"📊 Database contains:")
        print(f"   - {PricingTier.query.count()} pricing tiers")
        print(f"   - {Product.query.count()} products")
        print(f"   - {Retailer.query.count()} retailers")
        print(f"   - {Batch.query.count()} batches")
        print(f"   - {Order.query.count()} orders")


if __name__ == '__main__':
    main()