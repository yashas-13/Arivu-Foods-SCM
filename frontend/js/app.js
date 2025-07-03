/**
 * Arivu Foods SCMS Frontend Application
 * Mobile-first responsive dashboard for supply chain management
 */

const API_BASE_URL = '/api';

// Global application state
let currentSection = 'dashboard';
let products = [];
let retailers = [];
let pricingTiers = [];
let alerts = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Setup navigation
    setupNavigation();
    
    // Load initial data
    loadDashboard();
    loadPricingTiers();
    
    // Set up periodic updates
    setInterval(updateDashboard, 30000); // Update every 30 seconds
    setInterval(updateAlerts, 60000); // Update alerts every minute
}

function setupNavigation() {
    // Handle navbar links
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('href').substring(1);
            showSection(section);
        });
    });
}

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.add('d-none');
    });
    
    // Show selected section
    const targetSection = document.getElementById(sectionName);
    if (targetSection) {
        targetSection.classList.remove('d-none');
        currentSection = sectionName;
        
        // Load section-specific data
        switch(sectionName) {
            case 'dashboard':
                loadDashboard();
                break;
            case 'products':
                loadProducts();
                break;
            case 'batches':
                loadBatches();
                break;
            case 'orders':
                loadOrders();
                break;
            case 'retailers':
                loadRetailers();
                break;
            case 'alerts':
                loadAlerts();
                break;
        }
    }
}

// Dashboard Functions
async function loadDashboard() {
    try {
        // Load analytics data
        const [salesData, inventoryData] = await Promise.all([
            fetch(`${API_BASE_URL}/analytics/sales`).then(r => r.json()),
            fetch(`${API_BASE_URL}/analytics/inventory`).then(r => r.json())
        ]);
        
        // Update dashboard metrics
        updateDashboardMetrics(salesData, inventoryData);
        
        // Load recent alerts
        await loadRecentAlerts();
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard data');
    }
}

function updateDashboard() {
    if (currentSection === 'dashboard') {
        loadDashboard();
    }
}

function updateDashboardMetrics(salesData, inventoryData) {
    document.getElementById('total-sales').textContent = `₹${formatNumber(salesData.total_sales)}`;
    document.getElementById('total-inventory').textContent = `₹${formatNumber(inventoryData.total_inventory_value)}`;
    document.getElementById('low-stock-count').textContent = inventoryData.low_stock_items;
    document.getElementById('expiring-count').textContent = inventoryData.expiring_batches_7_days;
}

async function loadRecentAlerts() {
    try {
        const response = await fetch(`${API_BASE_URL}/alerts?status=New`);
        const alerts = await response.json();
        
        const alertsContainer = document.getElementById('recent-alerts');
        
        if (alerts.length === 0) {
            alertsContainer.innerHTML = '<p class="text-muted">No new alerts</p>';
            return;
        }
        
        alertsContainer.innerHTML = alerts.slice(0, 5).map(alert => `
            <div class="alert-card alert-${alert.alert_type.toLowerCase().replace(' ', '-')} p-3 mb-2">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${alert.alert_type}</strong>
                        <p class="mb-0">${alert.message}</p>
                        <small class="text-muted">${formatDate(alert.alert_date)}</small>
                    </div>
                    <span class="badge bg-${getAlertBadgeClass(alert.alert_type)}">${alert.status}</span>
                </div>
            </div>
        `).join('');
        
        // Update alert count in navbar
        document.getElementById('alert-count').textContent = alerts.length;
        
    } catch (error) {
        console.error('Error loading recent alerts:', error);
        document.getElementById('recent-alerts').innerHTML = '<p class="text-danger">Error loading alerts</p>';
    }
}

// Products Functions
async function loadProducts() {
    try {
        const response = await fetch(`${API_BASE_URL}/products`);
        products = await response.json();
        
        const tbody = document.getElementById('products-table-body');
        tbody.innerHTML = products.map(product => `
            <tr>
                <td>${product.sku}</td>
                <td>${product.product_name}</td>
                <td>${product.category || '-'}</td>
                <td>₹${product.mrp}</td>
                <td>${product.shelf_life_days || '-'} days</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewProduct(${product.product_id})">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="editProduct(${product.product_id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading products:', error);
        showError('Failed to load products');
    }
}

async function addProduct() {
    try {
        const productData = {
            sku: document.getElementById('productSku').value,
            product_name: document.getElementById('productName').value,
            category: document.getElementById('productCategory').value,
            brand: document.getElementById('productBrand').value,
            mrp: parseFloat(document.getElementById('productMrp').value),
            shelf_life_days: parseInt(document.getElementById('productShelfLife').value) || null,
            weight_per_unit: parseFloat(document.getElementById('productWeight').value) || null,
            unit_of_measure: document.getElementById('productUnitOfMeasure').value,
            description: document.getElementById('productDescription').value
        };
        
        const response = await fetch(`${API_BASE_URL}/products`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(productData)
        });
        
        if (response.ok) {
            showSuccess('Product added successfully');
            closeModal('addProductModal');
            loadProducts();
        } else {
            const error = await response.json();
            showError(`Failed to add product: ${error.error}`);
        }
        
    } catch (error) {
        console.error('Error adding product:', error);
        showError('Failed to add product');
    }
}

// Batches Functions
async function loadBatches() {
    try {
        const response = await fetch(`${API_BASE_URL}/batches`);
        const batches = await response.json();
        
        const tbody = document.getElementById('batches-table-body');
        tbody.innerHTML = batches.map(batch => `
            <tr>
                <td>${batch.manufacturer_batch_number}</td>
                <td>${batch.product ? batch.product.product_name : 'N/A'}</td>
                <td>${formatDate(batch.production_date)}</td>
                <td>${formatDate(batch.expiration_date)}</td>
                <td>${batch.current_quantity}</td>
                <td>
                    <span class="badge batch-status-${batch.status.toLowerCase().replace(' ', '-')}">${batch.status}</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewBatch(${batch.batch_id})">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="editBatch(${batch.batch_id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading batches:', error);
        showError('Failed to load batches');
    }
}

async function addBatch() {
    try {
        const batchData = {
            product_id: parseInt(document.getElementById('batchProductId').value),
            manufacturer_batch_number: document.getElementById('batchNumber').value,
            production_date: document.getElementById('batchProductionDate').value,
            expiration_date: document.getElementById('batchExpirationDate').value,
            initial_quantity: parseFloat(document.getElementById('batchInitialQuantity').value),
            current_quantity: parseFloat(document.getElementById('batchCurrentQuantity').value),
            manufacturing_location: document.getElementById('batchManufacturingLocation').value,
            status: 'In Stock'
        };
        
        const response = await fetch(`${API_BASE_URL}/batches`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(batchData)
        });
        
        if (response.ok) {
            showSuccess('Batch added successfully');
            closeModal('addBatchModal');
            loadBatches();
        } else {
            const error = await response.json();
            showError(`Failed to add batch: ${error.error}`);
        }
        
    } catch (error) {
        console.error('Error adding batch:', error);
        showError('Failed to add batch');
    }
}

// Orders Functions
async function loadOrders() {
    try {
        const response = await fetch(`${API_BASE_URL}/orders`);
        const orders = await response.json();
        
        const tbody = document.getElementById('orders-table-body');
        tbody.innerHTML = orders.map(order => `
            <tr>
                <td>#${order.order_id}</td>
                <td>${order.retailer ? order.retailer.retailer_name : 'N/A'}</td>
                <td>${formatDate(order.order_date)}</td>
                <td>₹${formatNumber(order.total_amount)}</td>
                <td>
                    <span class="badge bg-${getOrderStatusClass(order.order_status)}">${order.order_status}</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewOrder(${order.order_id})">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading orders:', error);
        showError('Failed to load orders');
    }
}

async function createOrder() {
    try {
        const orderItems = [];
        const orderItemElements = document.querySelectorAll('#orderItems .order-item');
        
        orderItemElements.forEach(element => {
            const productId = element.querySelector('select[name="productId"]').value;
            const quantity = element.querySelector('input[name="quantity"]').value;
            
            if (productId && quantity) {
                orderItems.push({
                    product_id: parseInt(productId),
                    quantity: parseFloat(quantity)
                });
            }
        });
        
        if (orderItems.length === 0) {
            showError('Please add at least one order item');
            return;
        }
        
        const orderData = {
            retailer_id: parseInt(document.getElementById('orderRetailerId').value),
            delivery_address: document.getElementById('orderDeliveryAddress').value,
            expected_delivery_date: document.getElementById('orderExpectedDeliveryDate').value,
            order_items: orderItems
        };
        
        const response = await fetch(`${API_BASE_URL}/orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        if (response.ok) {
            showSuccess('Order created successfully');
            closeModal('addOrderModal');
            loadOrders();
        } else {
            const error = await response.json();
            showError(`Failed to create order: ${error.error}`);
        }
        
    } catch (error) {
        console.error('Error creating order:', error);
        showError('Failed to create order');
    }
}

// Retailers Functions
async function loadRetailers() {
    try {
        const response = await fetch(`${API_BASE_URL}/retailers`);
        retailers = await response.json();
        
        const tbody = document.getElementById('retailers-table-body');
        tbody.innerHTML = retailers.map(retailer => `
            <tr>
                <td>${retailer.retailer_name}</td>
                <td>${retailer.contact_person || '-'}</td>
                <td>${retailer.city || '-'}</td>
                <td>${retailer.pricing_tier ? retailer.pricing_tier.tier_name : '-'}</td>
                <td>
                    <span class="badge bg-${getAccountStatusClass(retailer.account_status)}">${retailer.account_status}</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewRetailer(${retailer.retailer_id})">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="editRetailer(${retailer.retailer_id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading retailers:', error);
        showError('Failed to load retailers');
    }
}

async function addRetailer() {
    try {
        const retailerData = {
            retailer_name: document.getElementById('retailerName').value,
            contact_person: document.getElementById('retailerContactPerson').value,
            email: document.getElementById('retailerEmail').value,
            phone_number: document.getElementById('retailerPhone').value,
            address: document.getElementById('retailerAddress').value,
            city: document.getElementById('retailerCity').value,
            state: document.getElementById('retailerState').value,
            zip_code: document.getElementById('retailerZipCode').value,
            pricing_tier_id: parseInt(document.getElementById('retailerPricingTier').value) || null,
            account_status: 'Active'
        };
        
        const response = await fetch(`${API_BASE_URL}/retailers`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(retailerData)
        });
        
        if (response.ok) {
            showSuccess('Retailer added successfully');
            closeModal('addRetailerModal');
            loadRetailers();
        } else {
            const error = await response.json();
            showError(`Failed to add retailer: ${error.error}`);
        }
        
    } catch (error) {
        console.error('Error adding retailer:', error);
        showError('Failed to add retailer');
    }
}

// Alerts Functions
async function loadAlerts() {
    try {
        const response = await fetch(`${API_BASE_URL}/alerts`);
        alerts = await response.json();
        
        const container = document.getElementById('alerts-container');
        
        if (alerts.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No alerts found</p>';
            return;
        }
        
        container.innerHTML = alerts.map(alert => `
            <div class="alert-card alert-${alert.alert_type.toLowerCase().replace(' ', '-')} p-3 mb-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6><i class="fas fa-${getAlertIcon(alert.alert_type)} me-2"></i>${alert.alert_type}</h6>
                        <p class="mb-2">${alert.message}</p>
                        <small class="text-muted">
                            Created: ${formatDate(alert.alert_date)}
                            ${alert.threshold_value ? `| Threshold: ${alert.threshold_value}` : ''}
                        </small>
                    </div>
                    <div>
                        <span class="badge bg-${getAlertBadgeClass(alert.alert_type)} me-2">${alert.status}</span>
                        ${alert.status === 'New' ? `
                            <button class="btn btn-sm btn-outline-success" onclick="acknowledgeAlert(${alert.alert_id})">
                                <i class="fas fa-check"></i> Acknowledge
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading alerts:', error);
        showError('Failed to load alerts');
    }
}

async function generateExpirationAlerts() {
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/generate-expiration`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ days_ahead: 7 })
        });
        
        if (response.ok) {
            const result = await response.json();
            showSuccess(`Generated ${result.alerts_created} expiration alerts`);
            loadAlerts();
        } else {
            const error = await response.json();
            showError(`Failed to generate alerts: ${error.error}`);
        }
        
    } catch (error) {
        console.error('Error generating expiration alerts:', error);
        showError('Failed to generate expiration alerts');
    }
}

async function generateLowStockAlerts() {
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/generate-low-stock`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            showSuccess(`Generated ${result.alerts_created} low stock alerts`);
            loadAlerts();
        } else {
            const error = await response.json();
            showError(`Failed to generate alerts: ${error.error}`);
        }
        
    } catch (error) {
        console.error('Error generating low stock alerts:', error);
        showError('Failed to generate low stock alerts');
    }
}

// Modal Functions
function showAddProductModal() {
    const modal = new bootstrap.Modal(document.getElementById('addProductModal'));
    modal.show();
}

function showAddBatchModal() {
    loadProductsForDropdown('batchProductId');
    const modal = new bootstrap.Modal(document.getElementById('addBatchModal'));
    modal.show();
}

function showAddRetailerModal() {
    loadPricingTiersForDropdown('retailerPricingTier');
    const modal = new bootstrap.Modal(document.getElementById('addRetailerModal'));
    modal.show();
}

function showAddOrderModal() {
    loadRetailersForDropdown('orderRetailerId');
    loadProductsForOrderItems();
    const modal = new bootstrap.Modal(document.getElementById('addOrderModal'));
    modal.show();
}

function closeModal(modalId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (modal) {
        modal.hide();
    }
}

// Helper Functions for Dropdowns
async function loadProductsForDropdown(selectId) {
    try {
        if (products.length === 0) {
            const response = await fetch(`${API_BASE_URL}/products`);
            products = await response.json();
        }
        
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">Select product</option>' + 
            products.map(product => `<option value="${product.product_id}">${product.product_name} (${product.sku})</option>`).join('');
        
    } catch (error) {
        console.error('Error loading products for dropdown:', error);
    }
}

async function loadRetailersForDropdown(selectId) {
    try {
        if (retailers.length === 0) {
            const response = await fetch(`${API_BASE_URL}/retailers`);
            retailers = await response.json();
        }
        
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">Select retailer</option>' + 
            retailers.map(retailer => `<option value="${retailer.retailer_id}">${retailer.retailer_name}</option>`).join('');
        
    } catch (error) {
        console.error('Error loading retailers for dropdown:', error);
    }
}

async function loadPricingTiers() {
    try {
        const response = await fetch(`${API_BASE_URL}/pricing-tiers`);
        pricingTiers = await response.json();
    } catch (error) {
        console.error('Error loading pricing tiers:', error);
    }
}

async function loadPricingTiersForDropdown(selectId) {
    try {
        if (pricingTiers.length === 0) {
            await loadPricingTiers();
        }
        
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">Select pricing tier</option>' + 
            pricingTiers.map(tier => `<option value="${tier.tier_id}">${tier.tier_name} (${tier.min_discount_percentage}% - ${tier.max_discount_percentage}%)</option>`).join('');
        
    } catch (error) {
        console.error('Error loading pricing tiers for dropdown:', error);
    }
}

function loadProductsForOrderItems() {
    const orderItems = document.getElementById('orderItems');
    const selects = orderItems.querySelectorAll('select[name="productId"]');
    
    selects.forEach(select => {
        select.innerHTML = '<option value="">Select product</option>' + 
            products.map(product => `<option value="${product.product_id}">${product.product_name} (${product.sku})</option>`).join('');
    });
}

function addOrderItem() {
    const orderItems = document.getElementById('orderItems');
    const newItem = document.createElement('div');
    newItem.className = 'order-item row mb-2';
    newItem.innerHTML = `
        <div class="col-md-6">
            <select class="form-select" name="productId" required>
                <option value="">Select product</option>
                ${products.map(product => `<option value="${product.product_id}">${product.product_name} (${product.sku})</option>`).join('')}
            </select>
        </div>
        <div class="col-md-4">
            <input type="number" class="form-control" name="quantity" placeholder="Quantity" required>
        </div>
        <div class="col-md-2">
            <button type="button" class="btn btn-danger" onclick="removeOrderItem(this)">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    orderItems.appendChild(newItem);
}

function removeOrderItem(button) {
    const orderItems = document.getElementById('orderItems');
    if (orderItems.children.length > 1) {
        button.closest('.order-item').remove();
    }
}

function updateAlerts() {
    if (currentSection === 'alerts') {
        loadAlerts();
    }
    loadRecentAlerts(); // Always update recent alerts for dashboard
}

// Utility Functions
function formatNumber(num) {
    return new Intl.NumberFormat('en-IN').format(num);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN');
}

function getAlertBadgeClass(alertType) {
    switch(alertType) {
        case 'Expiration': return 'warning';
        case 'Low Stock': return 'danger';
        case 'Recall': return 'dark';
        case 'Quality Issue': return 'danger';
        default: return 'secondary';
    }
}

function getAlertIcon(alertType) {
    switch(alertType) {
        case 'Expiration': return 'calendar-times';
        case 'Low Stock': return 'exclamation-triangle';
        case 'Recall': return 'ban';
        case 'Quality Issue': return 'times-circle';
        default: return 'bell';
    }
}

function getOrderStatusClass(status) {
    switch(status) {
        case 'Pending': return 'warning';
        case 'Processing': return 'info';
        case 'Fulfilled': return 'success';
        case 'Shipped': return 'primary';
        case 'Delivered': return 'success';
        case 'Cancelled': return 'danger';
        default: return 'secondary';
    }
}

function getAccountStatusClass(status) {
    switch(status) {
        case 'Active': return 'success';
        case 'Inactive': return 'secondary';
        case 'On Hold': return 'warning';
        default: return 'secondary';
    }
}

// Toast Notifications
function showSuccess(message) {
    showToast(message, 'success');
}

function showError(message) {
    showToast(message, 'danger');
}

function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toastId = 'toast-' + Date.now();
    
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '1050';
    document.body.appendChild(container);
    return container;
}

// Placeholder functions for actions
function viewProduct(productId) {
    showError('Product view functionality not implemented yet');
}

function editProduct(productId) {
    showError('Product edit functionality not implemented yet');
}

function viewBatch(batchId) {
    showError('Batch view functionality not implemented yet');
}

function editBatch(batchId) {
    showError('Batch edit functionality not implemented yet');
}

function viewOrder(orderId) {
    showError('Order view functionality not implemented yet');
}

function viewRetailer(retailerId) {
    showError('Retailer view functionality not implemented yet');
}

function editRetailer(retailerId) {
    showError('Retailer edit functionality not implemented yet');
}

function acknowledgeAlert(alertId) {
    showError('Alert acknowledge functionality not implemented yet');
}