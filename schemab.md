# **Arivu Foods Supply Chain Management System \- Database Schema (Updated)**

This document outlines a proposed relational database schema for Arivu Foods' Supply Chain Management System (SCMS), designed to support core functionalities like batch management, dynamic pricing, sales analytics, and automated alerts. The schema focuses on key entities and their relationships, ensuring data consistency and efficient querying, now updated to reflect that there are only Arivu Foods (internal users) and Retailers (external partners), with no suppliers.

## **I. Overview of Entities**

The database will consist of several interconnected tables, each representing a core entity within the supply chain.

* **Products:** Stores master data for all food products.  
* **Batches:** Manages specific production lots of products, crucial for traceability and expiration.  
* **Retailers:** Contains information about Arivu Foods' distribution partners.  
* **PricingTiers:** Defines different discount levels or pricing models for retailers.  
* **Inventory:** Tracks stock levels for products within specific batches and locations.  
* **Orders:** Records customer orders placed by retailers.  
* **OrderItems:** Details the specific products and quantities within each order.  
* **Shipments:** Tracks the physical dispatch of products to retailers.  
* **QualityChecks:** Records quality control data for batches.  
* **Alerts:** Manages automated notifications for expiration and low stock.  
* **Users:** Manages user accounts within the SCMS (e.g., Arivu Foods staff).

## **II. Detailed Schema Definition**

### **1\. Products (Master Product Data)**

This table holds static, master data for each unique product that Arivu Foods distributes.

| Field Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| product\_id | UUID / INT | PRIMARY KEY, NOT NULL | Unique identifier for the product. |
| sku | VARCHAR(50) | UNIQUE, NOT NULL | Stock Keeping Unit \- internal unique identifier. |
| upc\_ean | VARCHAR(20) | UNIQUE | Universal Product Code / European Article Number. |
| product\_name | VARCHAR(255) | NOT NULL | Name of the product (e.g., "Organic Mango Pulp"). |
| description | TEXT |  | Detailed description of the product. |
| category | VARCHAR(100) |  | Product category (e.g., "Fruit Pulp", "Spices"). |
| brand | VARCHAR(100) |  | Brand name if different from Arivu Foods. |
| mrp | DECIMAL(10, 2\) | NOT NULL, \>= 0 | Manufacturer's Recommended Price per unit. |
| weight\_per\_unit | DECIMAL(10, 3\) | \>= 0 | Weight of a single unit (e.g., in kg). |
| unit\_of\_measure | VARCHAR(20) |  | Unit type (e.g., "kg", "dozen", "pouch"). |
| shelf\_life\_days | INT | \>= 0 | Standard shelf life of the product in days from production. |
| storage\_requirements | VARCHAR(255) |  | E.g., "Refrigerated", "Dry, Cool Place". |
| is\_perishable | BOOLEAN | DEFAULT TRUE | Indicates if the product is perishable. |
| created\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP | Timestamp of record creation. |
| updated\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP ON UPDATE CURRENT\_TIMESTAMP | Timestamp of last record update. |

### **2\. Batches (Product Lot Tracking)**

This table tracks specific production batches for each product, essential for traceability and expiration management.

| Field Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| batch\_id | UUID / INT | PRIMARY KEY, NOT NULL | Unique identifier for a product batch. |
| product\_id | UUID / INT | NOT NULL, FOREIGN KEY (Products.product\_id) | Links to the product it belongs to. |
| manufacturer\_batch\_number | VARCHAR(100) | NOT NULL | Batch number provided by the manufacturer. |
| production\_date | DATE | NOT NULL | Date the batch was produced. |
| expiration\_date | DATE | NOT NULL | Date the batch expires (calculated from production\_date \+ shelf\_life\_days). |
| initial\_quantity | DECIMAL(10, 2\) | NOT NULL, \>= 0 | Quantity received from the manufacturer. |
| current\_quantity | DECIMAL(10, 2\) | NOT NULL, \>= 0 | Current available quantity in this batch. |
| status | VARCHAR(50) | ENUM('Received', 'In Stock', 'Dispatched', 'Expired', 'Recalled'), NOT NULL | Current status of the batch. |
| manufacturing\_location | VARCHAR(255) |  | Location where the batch was manufactured. |
| created\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP | Timestamp of record creation. |
| updated\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP ON UPDATE CURRENT\_TIMESTAMP | Timestamp of last record update. |

### **3\. Retailers**

This table stores information about the retailers who purchase products from Arivu Foods.

| Field Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| retailer\_id | UUID / INT | PRIMARY KEY, NOT NULL | Unique identifier for the retailer. |
| retailer\_name | VARCHAR(255) | NOT NULL | Name of the retail store or chain. |
| contact\_person | VARCHAR(255) |  | Main contact person at the retailer. |
| email | VARCHAR(255) | UNIQUE | Retailer's primary email for communication. |
| phone\_number | VARCHAR(50) |  | Retailer's primary phone number. |
| address | TEXT |  | Physical address of the retailer. |
| city | VARCHAR(100) |  | City of the retailer. |
| state | VARCHAR(100) |  | State/Province of the retailer. |
| zip\_code | VARCHAR(20) |  | Postal/Zip code. |
| pricing\_tier\_id | UUID / INT | FOREIGN KEY (PricingTiers.tier\_id) | Links to their assigned pricing tier. |
| account\_status | VARCHAR(50) | ENUM('Active', 'Inactive', 'On Hold'), NOT NULL | Current status of the retailer account. |
| created\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP | Timestamp of record creation. |
| updated\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP ON UPDATE CURRENT\_TIMESTAMP | Timestamp of last record update. |

### **4\. PricingTiers**

This table defines different pricing tiers or discount structures applicable to retailers.

| Field Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| tier\_id | UUID / INT | PRIMARY KEY, NOT NULL | Unique identifier for the pricing tier. |
| tier\_name | VARCHAR(100) | UNIQUE, NOT NULL | Name of the tier (e.g., "Strategic Partner", "Key Account"). |
| min\_discount\_percentage | DECIMAL(5, 2\) | NOT NULL, \>= 0, \<= 100 | Minimum discount percentage allowed for this tier. |
| max\_discount\_percentage | DECIMAL(5, 2\) | NOT NULL, \>= 0, \<= 100 | Maximum discount percentage allowed for this tier. |
| description | TEXT |  | Description of the tier's criteria and benefits. |
| is\_active | BOOLEAN | DEFAULT TRUE | Indicates if the tier is currently active. |
| created\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP | Timestamp of record creation. |
| updated\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP ON UPDATE CURRENT\_TIMESTAMP | Timestamp of last record update. |

### **5\. Inventory (Stock Levels)**

This table tracks the quantity of each product for a specific batch in different locations (e.g., warehouse, in-transit).

| Field Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| inventory\_id | UUID / INT | PRIMARY KEY, NOT NULL | Unique identifier for an inventory record. |
| batch\_id | UUID / INT | NOT NULL, FOREIGN KEY (Batches.batch\_id) | Links to the specific product batch. |
| location | VARCHAR(255) | NOT NULL | Physical location of the inventory (e.g., "Main Warehouse", "Truck ID XYZ"). |
| quantity\_on\_hand | DECIMAL(10, 2\) | NOT NULL, \>= 0 | Current quantity of the batch at this location. |
| reorder\_point | DECIMAL(10, 2\) | \>= 0 | Quantity threshold to trigger a replenishment alert. |
| last\_updated\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP ON UPDATE CURRENT\_TIMESTAMP | Last time this inventory record was updated. |

### **6\. Orders (Retailer Orders)**

This table records details of orders placed by retailers.

| Field Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| order\_id | UUID / INT | PRIMARY KEY, NOT NULL | Unique identifier for the order. |
| retailer\_id | UUID / INT | NOT NULL, FOREIGN KEY (Retailers.retailer\_id) | Links to the retailer who placed the order. |
| order\_date | DATETIME | NOT NULL | Date and time the order was placed. |
| total\_amount | DECIMAL(12, 2\) | NOT NULL, \>= 0 | Total monetary value of the order. |
| order\_status | VARCHAR(50) | ENUM('Pending', 'Processing', 'Fulfilled', 'Shipped', 'Delivered', 'Cancelled'), NOT NULL | Current status of the order. |
| delivery\_address | TEXT | NOT NULL | Shipping address for this specific order. |
| expected\_delivery\_date | DATE |  | Expected date of delivery. |
| discount\_applied\_overall | DECIMAL(5, 2\) | DEFAULT 0.00 | Overall discount applied to the order (if any). |
| created\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP | Timestamp of record creation. |
| updated\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP ON UPDATE CURRENT\_TIMESTAMP | Timestamp of last record update. |

### **7\. OrderItems (Order Line Items)**

This table lists individual products and quantities within each order.

| Field Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| order\_item\_id | UUID / INT | PRIMARY KEY, NOT NULL | Unique identifier for an order line item. |
| order\_id | UUID / INT | NOT NULL, FOREIGN KEY (Orders.order\_id) | Links to the parent order. |
| product\_id | UUID / INT | NOT NULL, FOREIGN KEY (Products.product\_id) | Links to the product ordered. |
| batch\_id | UUID / INT | FOREIGN KEY (Batches.batch\_id) | The specific batch from which the product was fulfilled. (Can be NULL initially if allocation is later). |
| quantity | DECIMAL(10, 2\) | NOT NULL, \> 0 | Quantity of the product ordered. |
| unit\_price | DECIMAL(10, 2\) | NOT NULL, \>= 0 | Price of a single unit at the time of order. |
| line\_total | DECIMAL(12, 2\) | NOT NULL, \>= 0 | Total for this line item (quantity \* unit\_price). |
| discount\_percentage | DECIMAL(5, 2\) | DEFAULT 0.00 | Specific discount applied to this product in this order. |
| actual\_sales\_price | DECIMAL(10, 2\) | NOT NULL | The final price per unit after all discounts. |
| created\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP | Timestamp of record creation. |
| updated\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP ON UPDATE CURRENT\_TIMESTAMP | Timestamp of last record update. |

### **8\. Shipments**

This table tracks the logistics of product dispatch from Arivu Foods to retailers.

| Field Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| shipment\_id | UUID / INT | PRIMARY KEY, NOT NULL | Unique identifier for the shipment. |
| order\_id | UUID / INT | NOT NULL, FOREIGN KEY (Orders.order\_id) | Links to the order being shipped. |
| carrier\_name | VARCHAR(100) |  | Name of the shipping carrier (e.g., "Arivu Logistics", "FedEx"). |
| tracking\_number | VARCHAR(100) | UNIQUE | Tracking number for the shipment. |
| dispatch\_date | DATETIME | NOT NULL | Date and time the shipment was dispatched. |
| delivery\_date | DATETIME |  | Actual date and time of delivery. |
| shipment\_status | VARCHAR(50) | ENUM('Pending', 'In Transit', 'Delivered', 'Failed'), NOT NULL | Current status of the shipment. |
| estimated\_cost | DECIMAL(10, 2\) |  | Estimated shipping cost. |
| actual\_cost | DECIMAL(10, 2\) |  | Actual shipping cost. |
| created\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP | Timestamp of record creation. |
| updated\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP ON UPDATE CURRENT\_TIMESTAMP | Timestamp of last record update. |

### **9\. QualityChecks**

This table records results of quality inspections performed on batches.

| Field Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| check\_id | UUID / INT | PRIMARY KEY, NOT NULL | Unique identifier for a quality check. |
| batch\_id | UUID / INT | NOT NULL, FOREIGN KEY (Batches.batch\_id) | Links to the batch that was checked. |
| check\_date | DATETIME | NOT NULL | Date and time of the quality check. |
| checked\_by | UUID / INT | FOREIGN KEY (Users.user\_id) | User who performed the check. |
| result | VARCHAR(50) | ENUM('Pass', 'Fail', 'Conditional'), NOT NULL | Outcome of the quality check. |
| notes | TEXT |  | Any observations or details from the check. |
| issue\_description | TEXT |  | If failed, description of the issue. |
| created\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP | Timestamp of record creation. |
| updated\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP ON UPDATE CURRENT\_TIMESTAMP | Timestamp of last record update. |

### **10\. Alerts**

This table manages automated notifications for critical events.

| Field Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| alert\_id | UUID / INT | PRIMARY KEY, NOT NULL | Unique identifier for the alert. |
| alert\_type | VARCHAR(50) | ENUM('Expiration', 'Low Stock', 'Recall', 'Quality Issue'), NOT NULL | Type of alert. |
| target\_id | UUID / INT | NOT NULL | ID of the entity triggering the alert (e.g., batch\_id, retailer\_id). |
| target\_table | VARCHAR(50) | NOT NULL | Table name of the target entity (e.g., 'Batches', 'Retailers'). |
| message | TEXT | NOT NULL | Detailed message of the alert. |
| threshold\_value | DECIMAL(10, 2\) |  | The value that triggered the alert (e.g., stock quantity). |
| alert\_date | DATETIME | DEFAULT CURRENT\_TIMESTAMP | Date and time the alert was generated. |
| status | VARCHAR(50) | ENUM('New', 'Acknowledged', 'Resolved'), NOT NULL | Current status of the alert. |
| resolved\_by | UUID / INT | FOREIGN KEY (Users.user\_id) | User who resolved the alert. |
| resolved\_at | DATETIME |  | Timestamp when the alert was resolved. |
| created\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP | Timestamp of record creation. |
| updated\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP ON UPDATE CURRENT\_TIMESTAMP | Timestamp of last record update. |

### **11\. Users (SCMS Internal Users)**

This table stores information about users of the SCMS (Arivu Foods employees).

| Field Name | Data Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| user\_id | UUID / INT | PRIMARY KEY, NOT NULL | Unique identifier for the user. |
| username | VARCHAR(100) | UNIQUE, NOT NULL | User's login username. |
| password\_hash | VARCHAR(255) | NOT NULL | Hashed password for security. |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User's email address. |
| first\_name | VARCHAR(100) |  | User's first name. |
| last\_name | VARCHAR(100) |  | User's last name. |
| role | VARCHAR(50) | ENUM('Admin', 'Sales', 'Warehouse', 'Logistics', 'Quality Control'), NOT NULL | User's role in the system. |
| is\_active | BOOLEAN | DEFAULT TRUE | Indicates if the user account is active. |
| last\_login\_at | TIMESTAMP |  | Timestamp of the user's last login. |
| created\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP | Timestamp of record creation. |
| updated\_at | TIMESTAMP | DEFAULT CURRENT\_TIMESTAMP ON UPDATE CURRENT\_TIMESTAMP | Timestamp of last record update. |

## **III. Relationships (Foreign Keys)**

* Batches.product\_id \-\> Products.product\_id (One-to-Many: One product can have many batches)  
* Retailers.pricing\_tier\_id \-\> PricingTiers.tier\_id (Many-to-One: Many retailers can belong to one pricing tier)  
* Inventory.batch\_id \-\> Batches.batch\_id (Many-to-One: Many inventory records can refer to one batch)  
* Orders.retailer\_id \-\> Retailers.retailer\_id (Many-to-One: Many orders can be from one retailer)  
* OrderItems.order\_id \-\> Orders.order\_id (Many-to-One: Many order items belong to one order)  
* OrderItems.product\_id \-\> Products.product\_id (Many-to-One: Many order items can refer to one product)  
* OrderItems.batch\_id \-\> Batches.batch\_id (Many-to-One: Many order items can be fulfilled from one batch)  
* Shipments.order\_id \-\> Orders.order\_id (One-to-One/One-to-Many: One order can have one or more shipments if split)  
* QualityChecks.batch\_id \-\> Batches.batch\_id (Many-to-One: Many quality checks can be performed on one batch)  
* QualityChecks.checked\_by \-\> Users.user\_id (Many-to-One: Many quality checks can be performed by one user)  
* Alerts.target\_id (Contextual Foreign Key, depends on target\_table)  
* Alerts.resolved\_by \-\> Users.user\_id (Many-to-One: Many alerts can be resolved by one user)

## **IV. Indexing Strategy**

To optimize database performance, especially for frequent queries, the following indexes are recommended:

* **Primary Keys:** Automatically indexed.  
* **Foreign Keys:** Crucial for JOIN operations.  
  * product\_id in Batches, OrderItems  
  * pricing\_tier\_id in Retailers  
  * batch\_id in Inventory, OrderItems, QualityChecks  
  * retailer\_id in Orders  
  * order\_id in OrderItems, Shipments  
  * checked\_by in QualityChecks  
  * resolved\_by in Alerts  
* **Frequently Queried Columns:**  
  * sku in Products (for quick product lookup)  
  * manufacturer\_batch\_number in Batches (for tracing)  
  * expiration\_date in Batches (for expiration alerts)  
  * production\_date in Batches (for tracing)  
  * order\_date in Orders (for sales analytics)  
  * status in Batches, Orders, Shipments, Alerts (for filtering)  
  * retailer\_name in Retailers (for searching retailers)  
  * alert\_type in Alerts (for filtering alerts)

## **V. Considerations for Implementation**

* **Database System:** This schema is compatible with relational databases such as PostgreSQL, MySQL, SQL Server, or Oracle.  
* **Scalability:** For high-volume data, consider partitioning tables (e.g., OrderItems by date) or sharding.  
* **Data Types:** Choose appropriate data types to optimize storage and performance. Use DECIMAL for monetary values and quantities to avoid floating-point inaccuracies.  
* **UUID vs. INT Primary Keys:** UUIDs (Universally Unique Identifiers) are good for distributed systems and preventing ID clashes, while INT auto-incrementing IDs are simpler and often faster for single-instance databases. The choice depends on the anticipated scale and architecture.  
* **Auditing:** Consider adding created\_by and updated\_by fields (linked to the Users table) for better auditing and accountability.  
* **Data Archiving:** Plan a strategy for archiving old sales data or expired batch data that is no longer frequently accessed but needs to be retained for compliance.  
* **Denormalization (for Analytics):** For very complex or performance-critical analytical queries, a degree of denormalization might be considered (e.g., creating aggregated views or a separate data warehouse) to improve reporting speed, though this should be a later optimization.

This schema provides a solid foundation for building the Arivu Foods SCMS, enabling comprehensive data management and support for all identified functionalities.