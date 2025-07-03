from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'retailers', views.RetailerViewSet)
router.register(r'pricing-tiers', views.PricingTierViewSet)

urlpatterns = [
    path('pricing/', include(router.urls)),
    path('pricing/calculate/', views.CalculatePricingView.as_view(), name='calculate-pricing'),
    path('pricing/bulk-calculate/', views.BulkPricingView.as_view(), name='bulk-pricing'),
    path('pricing/expiry-discounts/', views.ExpiryDiscountsView.as_view(), name='expiry-discounts'),
    path('pricing/retailer-summary/<uuid:retailer_id>/', views.RetailerPricingSummaryView.as_view(), name='retailer-pricing-summary'),
]