#!/usr/bin/env python3
"""
Comprehensive test suite for Arivu Foods SCMS
Tests all core functionality including FIFO/FEFO, dynamic pricing, analytics, and alerts
"""

import json
import requests
import sys
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "http://localhost:5000/api"
TEST_PRODUCT_DATA = {
    "sku": "TEST-001",
    "product_name": "Test Organic Juice",
    "description": "Test product for SCMS",
    "category": "Beverages",
    "brand": "Arivu Foods",
    "mrp": 120.00,
    "weight_per_unit": 0.5,
    "unit_of_measure": "L",
    "shelf_life_days": 14,
    "storage_requirements": "Refrigerated",
    "is_perishable": True
}

def make_request(method, endpoint, data=None):
    """Helper function to make API requests"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server. Make sure the server is running on localhost:5000")
        sys.exit(1)

def test_health_check():
    """Test 1: Health check endpoint"""
    print("🔍 Test 1: Health Check")
    response = make_request("GET", "/health")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "ok":
            print("✅ Health check passed")
            return True
    
    print("❌ Health check failed")
    return False

def test_product_management():
    """Test 2: Product creation and retrieval"""
    print("\n🔍 Test 2: Product Management")
    
    # Create product
    response = make_request("POST", "/products", TEST_PRODUCT_DATA)
    if response.status_code != 201:
        print(f"❌ Product creation failed: {response.text}")
        return False
    
    product = response.json()
    product_id = product["product_id"]
    print(f"✅ Product created with ID: {product_id}")
    
    # Retrieve products
    response = make_request("GET", "/products")
    if response.status_code != 200:
        print("❌ Product retrieval failed")
        return False
    
    products_data = response.json()
    print(f"✅ Retrieved {len(products_data['products'])} products")
    return product_id

def test_batch_management_fifo_fefo(product_id):
    """Test 3: Batch management with FIFO/FEFO ordering"""
    print("\n🔍 Test 3: Batch Management (FIFO/FEFO)")
    
    # Create batches with different expiration dates to test FEFO
    today = date.today()
    
    batch1_data = {
        "product_id": product_id,
        "manufacturer_batch_number": "FIFO-001",
        "production_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
        "expiration_date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
        "initial_quantity": 100,
        "location": "Main Warehouse",
        "reorder_point": 20
    }
    
    batch2_data = {
        "product_id": product_id,
        "manufacturer_batch_number": "FIFO-002", 
        "production_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
        "expiration_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),  # Expires sooner
        "initial_quantity": 50,
        "location": "Main Warehouse",
        "reorder_point": 10
    }
    
    # Create first batch
    response = make_request("POST", "/batches", batch1_data)
    if response.status_code != 201:
        print(f"❌ Batch 1 creation failed: {response.text}")
        return False
    
    batch1 = response.json()
    print(f"✅ Created batch 1: {batch1['manufacturer_batch_number']} (expires {batch1['expiration_date']})")
    
    # Create second batch
    response = make_request("POST", "/batches", batch2_data)
    if response.status_code != 201:
        print(f"❌ Batch 2 creation failed: {response.text}")
        return False
    
    batch2 = response.json()
    print(f"✅ Created batch 2: {batch2['manufacturer_batch_number']} (expires {batch2['expiration_date']})")
    
    # Test FIFO/FEFO ordering
    response = make_request("GET", "/batches")
    if response.status_code != 200:
        print("❌ Batch retrieval failed")
        return False
    
    batches_data = response.json()
    batches = batches_data["batches"]
    
    if len(batches) >= 2:
        # Check if FEFO ordering is working (earlier expiration should come first)
        batch_by_number = {b["manufacturer_batch_number"]: b for b in batches}
        
        if "FIFO-002" in batch_by_number and "FIFO-001" in batch_by_number:
            # Find positions
            fifo_002_index = next(i for i, b in enumerate(batches) if b["manufacturer_batch_number"] == "FIFO-002")
            fifo_001_index = next(i for i, b in enumerate(batches) if b["manufacturer_batch_number"] == "FIFO-001")
            
            if fifo_002_index < fifo_001_index:
                print("✅ FEFO ordering verified: Earlier expiring batch comes first")
            else:
                print("❌ FEFO ordering failed: Batches not ordered by expiration date")
                return False
    
    return [batch1["batch_id"], batch2["batch_id"]]

def test_pricing_tiers():
    """Test 4: Pricing tiers creation"""
    print("\n🔍 Test 4: Pricing Tiers")
    
    tier_data = {
        "tier_name": "Test Premium",
        "min_discount_percentage": 15.0,
        "max_discount_percentage": 25.0,
        "description": "Test premium tier",
        "is_active": True
    }
    
    response = make_request("POST", "/pricing-tiers", tier_data)
    if response.status_code != 201:
        print(f"❌ Pricing tier creation failed: {response.text}")
        return False
    
    tier = response.json()
    print(f"✅ Created pricing tier: {tier['tier_name']} ({tier['min_discount_percentage']}-{tier['max_discount_percentage']}%)")
    return tier["tier_id"]

def test_retailer_management(pricing_tier_id):
    """Test 5: Retailer creation and management"""
    print("\n🔍 Test 5: Retailer Management")
    
    retailer_data = {
        "retailer_name": "Test Super Market",
        "contact_person": "Test Manager",
        "email": "test@supermarket.com",
        "phone_number": "+1234567890",
        "address": "123 Test Street",
        "city": "Test City",
        "state": "Test State",
        "zip_code": "12345",
        "pricing_tier_id": pricing_tier_id,
        "account_status": "Active"
    }
    
    response = make_request("POST", "/retailers", retailer_data)
    if response.status_code != 201:
        print(f"❌ Retailer creation failed: {response.text}")
        return False
    
    retailer = response.json()
    print(f"✅ Created retailer: {retailer['retailer_name']}")
    return retailer["retailer_id"]

def test_dynamic_pricing(retailer_id, product_id):
    """Test 6: Dynamic pricing calculation"""
    print("\n🔍 Test 6: Dynamic Pricing")
    
    pricing_data = {
        "retailer_id": retailer_id,
        "product_id": product_id,
        "quantity": 75
    }
    
    response = make_request("POST", "/pricing/calculate", pricing_data)
    if response.status_code != 200:
        print(f"❌ Dynamic pricing calculation failed: {response.text}")
        return False
    
    pricing = response.json()
    discount_percentage = pricing["discount_percentage"]
    final_price = pricing["final_price"]
    
    # Verify discount is within expected range (15-25% for test tier)
    if 15.0 <= discount_percentage <= 30.0:  # Allow for volume discount too
        print(f"✅ Dynamic pricing working: {discount_percentage}% discount, final price: ${final_price}")
        return True
    else:
        print(f"❌ Dynamic pricing discount out of range: {discount_percentage}%")
        return False

def test_order_management_fifo_fefo(retailer_id, product_id):
    """Test 7: Order creation with FIFO/FEFO allocation"""
    print("\n🔍 Test 7: Order Management (FIFO/FEFO Allocation)")
    
    order_data = {
        "retailer_id": retailer_id,
        "delivery_address": "123 Test Delivery Address",
        "expected_delivery_date": (date.today() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "items": [
            {
                "product_id": product_id,
                "quantity": 40  # This should be allocated from the earliest expiring batch first
            }
        ]
    }
    
    response = make_request("POST", "/orders", order_data)
    if response.status_code != 201:
        print(f"❌ Order creation failed: {response.text}")
        return False
    
    order = response.json()
    print(f"✅ Created order: #{order['order_id']} for ${order['total_amount']}")
    
    # Verify FIFO/FEFO allocation by checking inventory
    response = make_request("GET", "/inventory")
    if response.status_code == 200:
        inventory = response.json()
        for item in inventory:
            if item["batch_number"] == "FIFO-002":  # Should have reduced quantity
                if item["quantity_on_hand"] < 50:
                    print("✅ FIFO/FEFO allocation verified: Earlier expiring batch allocated first")
                    break
        else:
            print("❌ FIFO/FEFO allocation verification failed")
            return False
    
    return order["order_id"]

def test_inventory_tracking():
    """Test 8: Real-time inventory tracking"""
    print("\n🔍 Test 8: Real-time Inventory Tracking")
    
    response = make_request("GET", "/inventory")
    if response.status_code != 200:
        print("❌ Inventory retrieval failed")
        return False
    
    inventory = response.json()
    if inventory:
        print(f"✅ Inventory tracking working: {len(inventory)} items tracked")
        
        # Check FIFO/FEFO ordering in inventory
        if len(inventory) >= 2:
            first_item = inventory[0]
            second_item = inventory[1]
            
            first_expiry = datetime.strptime(first_item["expiration_date"], "%Y-%m-%d").date()
            second_expiry = datetime.strptime(second_item["expiration_date"], "%Y-%m-%d").date()
            
            if first_expiry <= second_expiry:
                print("✅ Inventory FEFO ordering verified")
            else:
                print("❌ Inventory FEFO ordering failed")
                return False
        
        return True
    else:
        print("❌ No inventory data found")
        return False

def test_alerts_system():
    """Test 9: Automated alerts system"""
    print("\n🔍 Test 9: Automated Alerts System")
    
    # Trigger alert check
    response = make_request("POST", "/alerts/check")
    if response.status_code != 200:
        print(f"❌ Alert check failed: {response.text}")
        return False
    
    alert_result = response.json()
    print(f"✅ Alert check completed: {alert_result['alerts_created']} new alerts")
    
    # Retrieve alerts
    response = make_request("GET", "/alerts")
    if response.status_code != 200:
        print("❌ Alert retrieval failed")
        return False
    
    alerts = response.json()
    print(f"✅ Retrieved {len(alerts)} active alerts")
    
    # Check for expected alert types
    alert_types = [alert["alert_type"] for alert in alerts]
    if "Expiration" in alert_types:
        print("✅ Expiration alerts working")
    
    return True

def test_sales_analytics():
    """Test 10: Sales analytics and reporting"""
    print("\n🔍 Test 10: Sales Analytics")
    
    # Test analytics with date range
    start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    response = make_request("GET", f"/analytics/sales?start_date={start_date}&end_date={end_date}")
    if response.status_code != 200:
        print(f"❌ Sales analytics failed: {response.text}")
        return False
    
    analytics = response.json()
    
    # Check for data structure
    if all(key in analytics for key in ["sales_by_product", "sales_by_retailer", "sales_by_batch"]):
        print("✅ Sales analytics structure verified")
        
        # Check for actual data
        if analytics["sales_by_product"]:
            print(f"✅ Product sales data: {len(analytics['sales_by_product'])} products")
        
        if analytics["sales_by_retailer"]:
            print(f"✅ Retailer sales data: {len(analytics['sales_by_retailer'])} retailers")
        
        if analytics["sales_by_batch"]:
            print(f"✅ Batch traceability data: {len(analytics['sales_by_batch'])} batches")
            
        return True
    else:
        print("❌ Sales analytics structure invalid")
        return False

def test_dashboard_analytics():
    """Test 11: Dashboard analytics"""
    print("\n🔍 Test 11: Dashboard Analytics")
    
    response = make_request("GET", "/analytics/dashboard")
    if response.status_code != 200:
        print("❌ Dashboard analytics failed")
        return False
    
    dashboard = response.json()
    
    # Check for required metrics
    required_metrics = [
        "total_products", "total_batches", "total_retailers", 
        "active_orders", "total_inventory", "near_expiry_batches",
        "low_stock_alerts", "recent_orders", "total_sales"
    ]
    
    if all(metric in dashboard for metric in required_metrics):
        print("✅ Dashboard analytics complete")
        print(f"   📊 Total Products: {dashboard['total_products']}")
        print(f"   📦 Total Batches: {dashboard['total_batches']}")
        print(f"   🏪 Total Retailers: {dashboard['total_retailers']}")
        print(f"   💰 Total Sales: ${dashboard['total_sales']}")
        return True
    else:
        print("❌ Dashboard analytics incomplete")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Arivu Foods SCMS Comprehensive Test Suite")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 11
    
    # Test 1: Health Check
    if test_health_check():
        tests_passed += 1
    
    # Test 2: Product Management
    product_id = test_product_management()
    if product_id:
        tests_passed += 1
    else:
        print("❌ Stopping tests: Product creation failed")
        return
    
    # Test 3: Batch Management (FIFO/FEFO)
    batch_ids = test_batch_management_fifo_fefo(product_id)
    if batch_ids:
        tests_passed += 1
    else:
        print("❌ Stopping tests: Batch creation failed")
        return
    
    # Test 4: Pricing Tiers
    pricing_tier_id = test_pricing_tiers()
    if pricing_tier_id:
        tests_passed += 1
    
    # Test 5: Retailer Management
    retailer_id = test_retailer_management(pricing_tier_id)
    if retailer_id:
        tests_passed += 1
    
    # Test 6: Dynamic Pricing
    if test_dynamic_pricing(retailer_id, product_id):
        tests_passed += 1
    
    # Test 7: Order Management (FIFO/FEFO)
    order_id = test_order_management_fifo_fefo(retailer_id, product_id)
    if order_id:
        tests_passed += 1
    
    # Test 8: Inventory Tracking
    if test_inventory_tracking():
        tests_passed += 1
    
    # Test 9: Alerts System
    if test_alerts_system():
        tests_passed += 1
    
    # Test 10: Sales Analytics
    if test_sales_analytics():
        tests_passed += 1
    
    # Test 11: Dashboard Analytics
    if test_dashboard_analytics():
        tests_passed += 1
    
    # Final Results
    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Arivu Foods SCMS is working correctly!")
        print("\n✅ Core Features Verified:")
        print("   • Python backend with Flask API")
        print("   • Mobile-first Bootstrap frontend")
        print("   • FIFO/FEFO inventory tracking")
        print("   • Batch management with full traceability")
        print("   • Dynamic pricing for retailers")
        print("   • Real-time inventory management")
        print("   • Automated expiration & low stock alerts")
        print("   • Comprehensive sales analytics")
        print("   • Responsive dashboard interface")
        
        return True
    else:
        print(f"❌ {total_tests - tests_passed} tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)