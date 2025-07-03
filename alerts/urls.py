from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'alerts', views.AlertViewSet)
router.register(r'alert-rules', views.AlertRuleViewSet)

urlpatterns = [
    path('alerts/', include(router.urls)),
    path('alerts/summary/', views.AlertSummaryView.as_view(), name='alert-summary'),
    path('alerts/run-checks/', views.RunAlertChecksView.as_view(), name='run-alert-checks'),
    path('alerts/active/', views.ActiveAlertsView.as_view(), name='active-alerts'),
    path('alerts/<uuid:alert_id>/acknowledge/', views.AcknowledgeAlertView.as_view(), name='acknowledge-alert'),
    path('alerts/<uuid:alert_id>/resolve/', views.ResolveAlertView.as_view(), name='resolve-alert'),
]