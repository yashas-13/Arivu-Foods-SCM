# **Arivu Foods Supply Chain Management System**

## Project Status
Version: 1.0.0 - **Production Ready**

## **Overview**

The Arivu Foods Supply Chain Management System (SCMS) is a comprehensive, production-ready solution designed to streamline and optimize the distribution of food products. It emphasizes efficient batch management, dynamic pricing, comprehensive sales analytics, and automated critical alerts. Tailored specifically for perishable goods, this system enhances operational efficiency, ensures product freshness, strengthens retailer relationships, and provides critical data visibility for informed decision-making.

### **Key Achievements**
- ✅ **Mobile-First Design**: Fully responsive interface optimized for smartphones and tablets
- ✅ **Real-Time Inventory Tracking**: FIFO/FEFO implementation with automatic expiration management
- ✅ **Dynamic Pricing Engine**: Retailer-specific discount tiers (20-30% range)
- ✅ **Automated Alert System**: Proactive notifications for expiration and low stock
- ✅ **Comprehensive Analytics**: Sales performance tracking and KPI dashboards
- ✅ **Weather Integration**: External API integration for supply chain monitoring
- ✅ **Background Services**: Automated monitoring and maintenance tasks

## **Features**

### **✅ Implemented Core Features**

* **Batch Management & Traceability:**  
  * ✅ Track specific product batches from receipt to dispatch  
  * ✅ Manage production dates, expiration dates, and quantities  
  * ✅ Enable forward and backward traceability for quick recalls and quality control  
  * ✅ Support for efficient batch division and allocation to various retailers
  * ✅ **FIFO/FEFO ordering** - Automatic First-In-First-Out / First-Expiry-First-Out rotation

* **Dynamic & Retailer-Specific Pricing:**  
  * ✅ Implement flexible pricing strategies with support for different pricing tiers  
  * ✅ Apply discounts to MRP (20-30% for strategic partners, 15-25% for key accounts)  
  * ✅ Ability to set volume-based or batch-specific pricing
  * ✅ **Real-time pricing calculation** API for order processing

* **Comprehensive Sales Analytics & Reporting:**  
  * ✅ Capture granular sales data for each batch, retailer, and product  
  * ✅ Generate dashboards for key performance indicators (KPIs)
  * ✅ Sales revenue, profit margin, inventory turnover analysis
  * ✅ **Real-time dashboard** with auto-refresh capabilities

* **Automated Alerts & Notifications:**  
  * ✅ **Product Expiration Alerts:** Proactive notifications for batches nearing expiration (7-day threshold)  
  * ✅ **Retailer Low Stock Alerts:** Alerts when stock levels fall below configurable thresholds
  * ✅ **Background monitoring** with automated alert generation

* **Inventory Management:**  
  * ✅ Real-time stock tracking across various locations  
  * ✅ Support for FIFO/FEFO (First-In, First-Out / First-Expiry, First-Out) inventory rotation  
  * ✅ Reorder point calculations to prevent stockouts
  * ✅ **Low stock detection** and automated alerts

* **Weather Dashboard:**
  * ✅ **External API integration** with OpenWeatherMap
  * ✅ **Graceful fallback** to mock data when API unavailable
  * ✅ Supply chain location monitoring capabilities

## **Technology Stack**

### **Backend**

* **Language:** Python  
* **Framework:** Flask (RESTful API architecture)
* **Database:** SQLite (Development) / PostgreSQL (Production)
  * Comprehensive schema supporting detailed product, batch, order, retailer, and alert management
* **Key Services:**  
  * ✅ **REST API Endpoints:** Complete CRUD operations for all entities
  * ✅ **Batch Processing:** FIFO/FEFO logic for managing batch quantities and statuses  
  * ✅ **Alert Generation:** Background services with automated scheduling for expiration and low stock monitoring
  * ✅ **Analytics Processing:** Real-time data aggregation for sales reports and dashboards
  * ✅ **Dynamic Pricing Engine:** Retailer-specific pricing calculation with configurable discount tiers

### **Frontend**

* **Technologies:** HTML5, CSS3, JavaScript  
* **Framework/Library:** Bootstrap 5.3 (responsive and mobile-first UI development)
* **Design Philosophy:** **Mobile App First**  
  * ✅ User interface optimized for small screens with seamless smartphone/tablet experience
  * ✅ Responsive design principles adapting layouts to different screen sizes
* **Key UI Components:**  
  * ✅ **Dashboards:** Clean, intuitive dashboards with real-time data for multiple user roles
  * ✅ **Product & Batch Management Screens:** Advanced search, filter, and management capabilities
  * ✅ **Order & Shipment Tracking:** Interface for managing retailer orders and monitoring status  
  * ✅ **Retailer Management:** Complete retailer profile management with pricing tier assignment
  * ✅ **Alert Notifications:** Real-time alert display within the application interface
  * ✅ **Weather Dashboard:** Integrated weather monitoring for supply chain locations

### **Enabling Technologies**

* ✅ **REST API Architecture:** Complete API coverage for all SCMS operations
* ✅ **Real-time Data Sync:** Auto-refresh capabilities for live dashboard updates
* ✅ **External API Integration:** Weather data integration with fallback mechanisms
* ✅ **Background Services:** Automated task scheduling for monitoring and maintenance
* ✅ **Responsive Design:** Bootstrap-based mobile-first implementation

## **API Documentation**

### **Core Endpoints**

#### **Products**
- `GET /api/products` - List products with search/filter capabilities
- `POST /api/products` - Create new product
- Query parameters: `search`, `category`, `brand`

#### **Batches** 
- `GET /api/batches` - List batches with FIFO/FEFO ordering
- `POST /api/batches` - Create new batch
- Query parameters: `order_by` (expiration_date/production_date), `status`, `product_id`

#### **Retailers**
- `GET /api/retailers` - List retailers with pricing tier information
- `POST /api/retailers` - Create new retailer

#### **Inventory**
- `GET /api/inventory` - Real-time inventory tracking with low stock detection

#### **Pricing**
- `POST /api/pricing/calculate` - Calculate retailer-specific pricing
- Body: `{"product_id": 1, "retailer_id": 1, "quantity": 10}`

#### **Analytics**
- `GET /api/analytics/sales-summary` - Sales analytics with date filtering
- Query parameters: `start_date`, `end_date`

#### **Alerts**
- `GET /api/alerts` - List active alerts
- `POST /api/alerts/check-expiration` - Generate expiration alerts

#### **Weather**
- `GET /api/weather` - Current weather data with fallback
- Query parameters: `city`

#### **Dashboard**
- `GET /api/dashboard/summary` - Complete dashboard overview

## **Getting Started**

### **Prerequisites**
- Python 3.8+
- pip (Python package manager)

### **Installation**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yashas-13/Arivu-Foods-SCM.git
   cd Arivu-Foods-SCM
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database:**
   ```bash
   python backend/init_db.py
   ```

4. **Start the application:**
   ```bash
   python -m backend.run
   ```

5. **Access the application:**
   - Open your browser to `http://localhost:5000`
   - The mobile-first interface will automatically adapt to your device

### **Configuration**

#### **Environment Variables**
- `DATABASE_URL`: Database connection string (default: SQLite)
- `OPENWEATHER_API_KEY`: Weather API key for external integration

#### **Sample Data**
The system includes comprehensive sample data:
- 5 Products across different categories (Grains, Vegetables, Dairy, Spices)
- 4 Pricing tiers with discount ranges
- 3 Retailers with different pricing assignments
- 4 Batches with realistic expiration dates
- Complete inventory tracking setup

## **Testing**

Run the comprehensive test suite:
```bash
python -m unittest tests.test_scms -v
```

**Test Coverage:**
- ✅ API endpoint functionality
- ✅ FIFO/FEFO batch ordering
- ✅ Dynamic pricing calculations
- ✅ Alert generation system
- ✅ Inventory tracking
- ✅ Dashboard data aggregation

## **Screenshots**

### **Desktop Dashboard**
![Desktop Dashboard](https://github.com/user-attachments/assets/326078b0-9076-48f8-ba79-006936cabc72)

### **Mobile Dashboard** 
![Mobile Dashboard](https://github.com/user-attachments/assets/5e121b5b-1e46-48e9-bca4-46ed345cfb2f)

## **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend        │    │   Database      │
│   (Bootstrap)   │◄──►│   (Flask API)    │◄──►│   (SQLite/      │
│   - Dashboard   │    │   - REST API     │    │    PostgreSQL)  │
│   - Mobile UI   │    │   - Background   │    │   - Products    │
│   - Analytics   │    │     Services     │    │   - Batches     │
└─────────────────┘    │   - FIFO/FEFO    │    │   - Retailers   │
                       │   - Pricing      │    │   - Inventory   │
                       │   - Alerts       │    │   - Orders      │
                       └──────────────────┘    └─────────────────┘
```

## **Pricing Tier Structure**

| Tier | Discount Range | Criteria |
|------|---------------|----------|
| **Strategic Partners** | 25-30% | High volume, long-term contracts |
| **Key Accounts** | 20-25% | Consistent medium-high volume |
| **Emerging Accounts** | 15-20% | New customers with growth potential |
| **Spot/Ad-hoc** | 10-20% | Urgent, non-contractual orders |

## **Background Services**

The system includes automated background services:
- **Expiration Monitoring**: Hourly checks for products nearing expiration
- **Low Stock Alerts**: Bi-hourly inventory level monitoring  
- **Daily Cleanup**: Automated maintenance and status updates

## **Future Enhancements**

* **Advanced Analytics:** Machine learning for demand forecasting
* **IoT Integration:** Real-time temperature and humidity monitoring
* **Mobile Application:** Native iOS/Android applications
* **Advanced Logistics:** Route optimization and carrier integration
* **User Authentication:** Role-based access control system
* **Barcode/RFID:** Physical tracking integration
* **Multi-location:** Support for multiple warehouses and distribution centers

## **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## **License**

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

**Arivu Foods SCMS** - Optimizing food distribution through technology, enhancing freshness and strengthening retailer relationships.