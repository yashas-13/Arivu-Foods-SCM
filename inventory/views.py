from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Product, Batch, Inventory
from .services import InventoryService
from .serializers import ProductSerializer, BatchSerializer, InventorySerializer

# Create your views here.

class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = []  # Allow unauthenticated access for development
    
    def get_queryset(self):
        queryset = Product.objects.all()
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)
        
        if search:
            queryset = queryset.filter(
                Q(product_name__icontains=search) |
                Q(sku__icontains=search) |
                Q(description__icontains=search)
            )
        
        if category:
            queryset = queryset.filter(category=category)
            
        return queryset.order_by('product_name')


class BatchViewSet(viewsets.ModelViewSet):
    """ViewSet for Batch model."""
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Batch.objects.all()
        product_id = self.request.query_params.get('product', None)
        status = self.request.query_params.get('status', None)
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
            
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-production_date')


class InventoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Inventory model."""
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Inventory.objects.all()
        location = self.request.query_params.get('location', None)
        product_id = self.request.query_params.get('product', None)
        
        if location:
            queryset = queryset.filter(location=location)
            
        if product_id:
            queryset = queryset.filter(batch__product_id=product_id)
            
        return queryset.order_by('location', 'batch__expiration_date')


class ExpiryAlertsView(APIView):
    """API view for expiry alerts."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        days_ahead = int(request.query_params.get('days', 7))
        alerts = InventoryService.get_expiry_alerts(days_ahead)
        
        return Response({
            'alerts': alerts,
            'total_alerts': len(alerts),
            'days_ahead': days_ahead
        })


class LowStockAlertsView(APIView):
    """API view for low stock alerts."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        location = request.query_params.get('location', None)
        alerts = InventoryService.get_low_stock_alerts(location)
        
        return Response({
            'alerts': alerts,
            'total_alerts': len(alerts),
            'location': location
        })


class InventorySummaryView(APIView):
    """API view for inventory summary."""
    permission_classes = []  # Allow unauthenticated access for development
    
    def get(self, request):
        location = request.query_params.get('location', None)
        summary = InventoryService.get_inventory_summary(location)
        
        return Response(summary)


class FIFOAllocationView(APIView):
    """API view for FIFO allocation."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            quantity = float(request.data.get('quantity', 0))
            location = request.data.get('location')
            
            if not product_id or quantity <= 0:
                return Response(
                    {'error': 'Product ID and valid quantity are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                product = Product.objects.get(product_id=product_id)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            result = InventoryService.fulfill_order_item(
                product, quantity, location, method='fifo'
            )
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FEFOAllocationView(APIView):
    """API view for FEFO allocation."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            quantity = float(request.data.get('quantity', 0))
            location = request.data.get('location')
            
            if not product_id or quantity <= 0:
                return Response(
                    {'error': 'Product ID and valid quantity are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                product = Product.objects.get(product_id=product_id)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            result = InventoryService.fulfill_order_item(
                product, quantity, location, method='fefo'
            )
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
