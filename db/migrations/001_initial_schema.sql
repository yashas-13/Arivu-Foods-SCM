-- Initial schema for Arivu Foods SCMS
-- Reference: schemadb.md - Section II. Detailed Schema Definition
BEGIN;

-- Table: PricingTiers (see schemadb.md - II.4 PricingTiers)
CREATE TABLE IF NOT EXISTS PricingTiers (
    tier_id SERIAL PRIMARY KEY,
    tier_name VARCHAR(100) UNIQUE NOT NULL,
    min_discount_percentage DECIMAL(5,2) NOT NULL CHECK (min_discount_percentage >= 0 AND min_discount_percentage <= 100),
    max_discount_percentage DECIMAL(5,2) NOT NULL CHECK (max_discount_percentage >= 0 AND max_discount_percentage <= 100),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Products (see schemadb.md - II.1 Products)
CREATE TABLE IF NOT EXISTS Products (
    product_id SERIAL PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE,
    upc_ean VARCHAR(20) UNIQUE,
    product_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    brand VARCHAR(100),
    mrp DECIMAL(10,2) NOT NULL CHECK (mrp >= 0),
    weight_per_unit DECIMAL(10,3) CHECK (weight_per_unit >= 0),
    unit_of_measure VARCHAR(20),
    shelf_life_days INT CHECK (shelf_life_days >= 0),
    storage_requirements VARCHAR(255),
    is_perishable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Batches (see schemadb.md - II.2 Batches)
CREATE TABLE IF NOT EXISTS Batches (
    batch_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES Products(product_id),
    manufacturer_batch_number VARCHAR(100) NOT NULL,
    production_date DATE NOT NULL,
    expiration_date DATE NOT NULL,
    initial_quantity DECIMAL(10,2) NOT NULL CHECK (initial_quantity >= 0),
    current_quantity DECIMAL(10,2) NOT NULL CHECK (current_quantity >= 0),
    status VARCHAR(50) NOT NULL CHECK (status IN ('Received','In Stock','Dispatched','Expired','Recalled')),
    manufacturing_location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Retailers (see schemadb.md - II.3 Retailers)
CREATE TABLE IF NOT EXISTS Retailers (
    retailer_id SERIAL PRIMARY KEY,
    retailer_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    pricing_tier_id INT REFERENCES PricingTiers(tier_id),
    account_status VARCHAR(50) NOT NULL CHECK (account_status IN ('Active','Inactive','On Hold')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Inventory (see schemadb.md - II.5 Inventory)
CREATE TABLE IF NOT EXISTS Inventory (
    inventory_id SERIAL PRIMARY KEY,
    batch_id INT NOT NULL REFERENCES Batches(batch_id),
    location VARCHAR(255) NOT NULL,
    quantity_on_hand DECIMAL(10,2) NOT NULL CHECK (quantity_on_hand >= 0),
    reorder_point DECIMAL(10,2) CHECK (reorder_point >= 0),
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Orders (see schemadb.md - II.6 Orders)
CREATE TABLE IF NOT EXISTS Orders (
    order_id SERIAL PRIMARY KEY,
    retailer_id INT NOT NULL REFERENCES Retailers(retailer_id),
    order_date TIMESTAMP NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL CHECK (total_amount >= 0),
    order_status VARCHAR(50) NOT NULL CHECK (order_status IN ('Pending','Processing','Fulfilled','Shipped','Delivered','Cancelled')),
    delivery_address TEXT NOT NULL,
    expected_delivery_date DATE,
    discount_applied_overall DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: OrderItems (see schemadb.md - II.7 OrderItems)
CREATE TABLE IF NOT EXISTS OrderItems (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES Orders(order_id),
    product_id INT NOT NULL REFERENCES Products(product_id),
    batch_id INT REFERENCES Batches(batch_id),
    quantity DECIMAL(10,2) NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    line_total DECIMAL(12,2) NOT NULL CHECK (line_total >= 0),
    discount_percentage DECIMAL(5,2) DEFAULT 0.00,
    actual_sales_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Shipments (see schemadb.md - II.8 Shipments)
CREATE TABLE IF NOT EXISTS Shipments (
    shipment_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES Orders(order_id),
    carrier_name VARCHAR(100),
    tracking_number VARCHAR(100) UNIQUE,
    dispatch_date TIMESTAMP NOT NULL,
    delivery_date TIMESTAMP,
    shipment_status VARCHAR(50) NOT NULL CHECK (shipment_status IN ('Pending','In Transit','Delivered','Failed')),
    estimated_cost DECIMAL(10,2),
    actual_cost DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Users (see schemadb.md - II.11 Users)
CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) NOT NULL CHECK (role IN ('Admin','Sales','Warehouse','Logistics','Quality Control')),
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: QualityChecks (see schemadb.md - II.9 QualityChecks)
CREATE TABLE IF NOT EXISTS QualityChecks (
    check_id SERIAL PRIMARY KEY,
    batch_id INT NOT NULL REFERENCES Batches(batch_id),
    check_date TIMESTAMP NOT NULL,
    checked_by INT REFERENCES Users(user_id),
    result VARCHAR(50) NOT NULL CHECK (result IN ('Pass','Fail','Conditional')),
    notes TEXT,
    issue_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Alerts (see schemadb.md - II.10 Alerts)
CREATE TABLE IF NOT EXISTS Alerts (
    alert_id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('Expiration','Low Stock','Recall','Quality Issue')),
    target_id INT NOT NULL,
    target_table VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    threshold_value DECIMAL(10,2),
    alert_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL CHECK (status IN ('New','Acknowledged','Resolved')),
    resolved_by INT REFERENCES Users(user_id),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes (see schemadb.md - Section IV Indexing Strategy)
CREATE INDEX IF NOT EXISTS idx_batches_product_id ON Batches(product_id);
CREATE INDEX IF NOT EXISTS idx_retailers_pricing_tier_id ON Retailers(pricing_tier_id);
CREATE INDEX IF NOT EXISTS idx_inventory_batch_id ON Inventory(batch_id);
CREATE INDEX IF NOT EXISTS idx_orders_retailer_id ON Orders(retailer_id);
CREATE INDEX IF NOT EXISTS idx_orderitems_order_id ON OrderItems(order_id);
CREATE INDEX IF NOT EXISTS idx_orderitems_product_id ON OrderItems(product_id);
CREATE INDEX IF NOT EXISTS idx_orderitems_batch_id ON OrderItems(batch_id);
CREATE INDEX IF NOT EXISTS idx_shipments_order_id ON Shipments(order_id);
CREATE INDEX IF NOT EXISTS idx_qualitychecks_batch_id ON QualityChecks(batch_id);
CREATE INDEX IF NOT EXISTS idx_qualitychecks_checked_by ON QualityChecks(checked_by);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved_by ON Alerts(resolved_by);

-- Frequently queried columns
CREATE INDEX IF NOT EXISTS idx_products_sku ON Products(sku);
CREATE INDEX IF NOT EXISTS idx_batches_manufacturer_number ON Batches(manufacturer_batch_number);
CREATE INDEX IF NOT EXISTS idx_batches_expiration_date ON Batches(expiration_date);
CREATE INDEX IF NOT EXISTS idx_batches_production_date ON Batches(production_date);
CREATE INDEX IF NOT EXISTS idx_batches_status ON Batches(status);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON Orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status ON Orders(order_status);
CREATE INDEX IF NOT EXISTS idx_shipments_status ON Shipments(shipment_status);
CREATE INDEX IF NOT EXISTS idx_retailers_name ON Retailers(retailer_name);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON Alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON Alerts(status);

COMMIT;
