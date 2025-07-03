from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import date, timedelta
from .models import Order, OrderItem, SalesTransaction
from .services import AnalyticsService
from .serializers import OrderSerializer, OrderItemSerializer
from inventory.models import Product, Batch
from pricing.models import Retailer

# Create your views here.

class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order model."""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


class OrderItemViewSet(viewsets.ModelViewSet):
    """ViewSet for OrderItem model."""
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]


class DashboardMetricsView(APIView):
    """API view for dashboard metrics."""
    permission_classes = []  # Allow unauthenticated access for development
    
    def get(self, request):
        try:
            period_days = int(request.query_params.get('days', 30))
            metrics = AnalyticsService.get_dashboard_metrics(period_days)
            return Response(metrics)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SalesOverviewView(APIView):
    """API view for sales overview."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            # Parse date parameters if provided
            start_param = request.query_params.get('start_date')
            end_param = request.query_params.get('end_date')
            
            if start_param:
                start_date = date.fromisoformat(start_param)
            if end_param:
                end_date = date.fromisoformat(end_param)
            
            overview = AnalyticsService.get_sales_overview(start_date, end_date)
            return Response(overview)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductPerformanceView(APIView):
    """API view for product performance."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, product_id):
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            try:
                product = Product.objects.get(product_id=product_id)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            performance = AnalyticsService.get_product_performance(product, start_date, end_date)
            return Response(performance)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RetailerPerformanceView(APIView):
    """API view for retailer performance."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, retailer_id):
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            try:
                retailer = Retailer.objects.get(retailer_id=retailer_id)
            except Retailer.DoesNotExist:
                return Response(
                    {'error': 'Retailer not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            performance = AnalyticsService.get_retailer_performance(retailer, start_date, end_date)
            return Response(performance)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InventoryAnalyticsView(APIView):
    """API view for inventory analytics."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            analytics = AnalyticsService.get_inventory_analytics(start_date, end_date)
            return Response(analytics)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BatchAnalyticsView(APIView):
    """API view for batch analytics."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, batch_id):
        try:
            try:
                batch = Batch.objects.get(batch_id=batch_id)
            except Batch.DoesNotExist:
                return Response(
                    {'error': 'Batch not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            analytics = AnalyticsService.get_batch_analytics(batch)
            return Response(analytics)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
