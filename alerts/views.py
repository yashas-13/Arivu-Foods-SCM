from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Alert, AlertRule, AlertSubscription
from .services import AlertService
from .serializers import AlertSerializer, AlertRuleSerializer

# Create your views here.

class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet for Alert model."""
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Alert.objects.all()
        status_filter = self.request.query_params.get('status', None)
        alert_type = self.request.query_params.get('type', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
            
        return queryset.order_by('-created_at')


class AlertRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for AlertRule model."""
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAuthenticated]


class AlertSummaryView(APIView):
    """API view for alert summary."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            summary = AlertService.get_alert_summary()
            return Response(summary)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RunAlertChecksView(APIView):
    """API view to run alert checks."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            results = AlertService.run_alert_checks()
            return Response(results)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ActiveAlertsView(APIView):
    """API view for active alerts."""
    permission_classes = []  # Allow unauthenticated access for development
    
    def get(self, request):
        try:
            alert_type = request.query_params.get('type')
            priority = request.query_params.get('priority')
            
            # Don't filter by user for unauthenticated access
            alerts = AlertService.get_active_alerts(
                user=None,
                alert_type=alert_type,
                priority=priority
            )
            
            serializer = AlertSerializer(alerts, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AcknowledgeAlertView(APIView):
    """API view to acknowledge an alert."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, alert_id):
        try:
            try:
                alert = Alert.objects.get(alert_id=alert_id)
            except Alert.DoesNotExist:
                return Response(
                    {'error': 'Alert not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            alert.acknowledge(request.user)
            
            return Response({
                'message': 'Alert acknowledged successfully',
                'alert_id': str(alert_id)
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResolveAlertView(APIView):
    """API view to resolve an alert."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, alert_id):
        try:
            try:
                alert = Alert.objects.get(alert_id=alert_id)
            except Alert.DoesNotExist:
                return Response(
                    {'error': 'Alert not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            alert.resolve(request.user)
            
            return Response({
                'message': 'Alert resolved successfully',
                'alert_id': str(alert_id)
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
