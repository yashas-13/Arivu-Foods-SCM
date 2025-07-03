from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet)
router.register(r'order-items', views.OrderItemViewSet)

urlpatterns = [
    path('analytics/', include(router.urls)),
    path('analytics/dashboard/', views.DashboardMetricsView.as_view(), name='dashboard-metrics'),
    path('analytics/sales-overview/', views.SalesOverviewView.as_view(), name='sales-overview'),
    path('analytics/product-performance/<uuid:product_id>/', views.ProductPerformanceView.as_view(), name='product-performance'),
    path('analytics/retailer-performance/<uuid:retailer_id>/', views.RetailerPerformanceView.as_view(), name='retailer-performance'),
    path('analytics/inventory-analytics/', views.InventoryAnalyticsView.as_view(), name='inventory-analytics'),
    path('analytics/batch-analytics/<uuid:batch_id>/', views.BatchAnalyticsView.as_view(), name='batch-analytics'),
]