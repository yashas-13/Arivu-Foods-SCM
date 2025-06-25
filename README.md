# **Arivu Foods Supply Chain Management System**

## Project Status
Version: 0.1.0

## **Overview**

The Arivu Foods Supply Chain Management System (SCMS) is designed to streamline and optimize the distribution of food products, emphasizing efficient batch management, dynamic pricing, comprehensive sales analytics, and automated critical alerts. Tailored for perishable goods, this system aims to enhance operational efficiency, ensure product freshness, strengthen retailer relationships, and provide critical data visibility for informed decision-making.

## **Features**

* **Batch Management & Traceability:**  
  * Track specific product batches from receipt to dispatch.  
  * Manage production dates, expiration dates, and quantities.  
  * Enable forward and backward traceability for quick recalls and quality control.  
  * Support for efficient batch division and allocation to various retailers.  
* **Dynamic & Retailer-Specific Pricing:**  
  * Implement flexible pricing strategies with support for different pricing tiers.  
  * Apply discounts to MRP (e.g., 20-30% for retailers).  
  * Ability to set volume-based or batch-specific pricing.  
* **Comprehensive Sales Analytics & Reporting:**  
  * Capture granular sales data for each batch, retailer, and product.  
  * Generate dashboards for key performance indicators (KPIs) like sales revenue, profit margin, inventory turnover, and on-time delivery.  
  * Analyze sales trends and identify opportunities for growth.  
* **Automated Alerts & Notifications:**  
  * **Product Expiration Alerts:** Proactive notifications for batches nearing their expiration date.  
  * **Retailer Low Stock Alerts:** Alerts for retailers when their inferred or reported stock levels fall below a configurable threshold, prompting replenishment.  
* **Inventory Management:**  
  * Real-time stock tracking across various locations.  
  * Support for FIFO/FEFO (First-In, First-Out / First-Expiry, First-Out) inventory rotation.  
  * Reorder point calculations to prevent stockouts.

## **Technology Stack**

### **Backend**

* **Language:** Python  
  * *(Potential Frameworks: Flask, Django \- for robust web applications and API development)*  
* **Database:** Relational Database (e.g., PostgreSQL, MySQL, SQLite)  
  * The database schema is designed to support detailed product, batch, order, retailer, and alert management.  
* **Key Services:**  
  * **API Endpoints:** For communication with the frontend, enabling data retrieval and updates.  
  * **Batch Processing:** Logic for managing batch quantities and statuses.  
  * **Alert Generation:** Background tasks or cron jobs to check for expiration and low stock conditions and trigger alerts.  
  * **Analytics Processing:** Data aggregation and computation for sales reports and dashboards.

### **Frontend**

* **Technologies:** HTML5, CSS3, JavaScript  
* **Framework/Library:** Bootstrap (for responsive and mobile-first UI development)  
* **Design Philosophy:** Mobile App First  
  * User interface will be optimized for small screens, ensuring a seamless experience on smartphones and tablets.  
  * Responsive design principles will be used to adapt layouts to different screen sizes.  
* **Key UI Components:**  
  * **Dashboards:** Clean, intuitive dashboards for Arivu Foods users (admin, sales, warehouse) to view sales, inventory, and alerts.  
  * **Product & Batch Management Screens:** Forms for adding/editing products and batches, with search and filter capabilities.  
  * **Order & Shipment Tracking:** Interfaces for managing retailer orders and monitoring shipment status.  
  * **Retailer Management:** Pages to view and update retailer details, including their assigned pricing tiers.  
  * **Alert Notifications:** Clear display of active alerts within the application.

### **Enabling Technologies (Integrated or Planned)**

* **Barcode/RFID Integration:** For efficient receiving, inventory counts, and dispatch.  
* **IoT (Internet of Things):** (Future consideration) Sensors for real-time temperature/humidity monitoring of perishable goods during storage and transit.  
* **AI/ML (Artificial Intelligence/Machine Learning):** (Future consideration) For advanced demand forecasting, route optimization, and more sophisticated dynamic pricing algorithms.

## **Getting Started (High-Level)**

1. **Clone the Repository:**  
   git clone https://github.com/arivufoods/supply-chain-management-system.git  
   cd supply-chain-management-system

2. **Backend Setup (Python):**  
   * Set up a Python virtual environment.  
   * Install required Python packages (e.g., Flask, SQLAlchemy or Django, psycopg2 for PostgreSQL).  
   * Configure your database connection.  
   * Run database migrations to create the schema. Use the SQL files in `db/migrations`.  
   * Start the backend server.  
3. **Frontend Setup (HTML/Bootstrap):**  
   * Open the index.html file in your web browser.  
   * Ensure all necessary Bootstrap and custom CSS/JS files are linked correctly.

*(Detailed installation and configuration instructions will be provided in a separate CONTRIBUTING.md or INSTALL.md file.)*

## Recent Changes
* Added initial migration scripts under db/migrations.
* Database schema now implemented as per schemadb.md.

## **Future Enhancements**

* Integration with payment gateways.  
* Enhanced reporting and custom report generation.  
* Mobile application development (native or PWA).  
* Integration with external logistics providers.  
* Advanced AI/ML models for predictive analytics.

## **Contributing**

We welcome contributions\! Please see CONTRIBUTING.md for guidelines.

## **License**

This project is licensed under the MIT License. See the LICENSE file for details.
