from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'batches', views.BatchViewSet)
router.register(r'inventory', views.InventoryViewSet)

urlpatterns = [
    path('inventory/', include(router.urls)),
    path('inventory/alerts/expiry/', views.ExpiryAlertsView.as_view(), name='expiry-alerts'),
    path('inventory/alerts/low-stock/', views.LowStockAlertsView.as_view(), name='low-stock-alerts'),
    path('inventory/summary/', views.InventorySummaryView.as_view(), name='inventory-summary'),
    path('inventory/fifo-allocation/', views.FIFOAllocationView.as_view(), name='fifo-allocation'),
    path('inventory/fefo-allocation/', views.FEFOAllocationView.as_view(), name='fefo-allocation'),
]