from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Retailer, PricingTier, RetailerPricing
from .services import PricingService
from .serializers import RetailerSerializer, PricingTierSerializer
from inventory.models import Product

# Create your views here.

class RetailerViewSet(viewsets.ModelViewSet):
    """ViewSet for Retailer model."""
    queryset = Retailer.objects.all()
    serializer_class = RetailerSerializer
    permission_classes = []  # Allow unauthenticated access for development


class PricingTierViewSet(viewsets.ModelViewSet):
    """ViewSet for PricingTier model."""
    queryset = PricingTier.objects.all()
    serializer_class = PricingTierSerializer
    permission_classes = [IsAuthenticated]


class CalculatePricingView(APIView):
    """API view for calculating pricing for a retailer-product combination."""
    permission_classes = []  # Allow unauthenticated access for development
    
    def post(self, request):
        try:
            retailer_id = request.data.get('retailer_id')
            product_id = request.data.get('product_id')
            quantity = float(request.data.get('quantity', 1))
            
            if not retailer_id or not product_id:
                return Response(
                    {'error': 'Retailer ID and Product ID are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                retailer = Retailer.objects.get(retailer_id=retailer_id)
                product = Product.objects.get(product_id=product_id)
            except (Retailer.DoesNotExist, Product.DoesNotExist):
                return Response(
                    {'error': 'Retailer or Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            pricing = PricingService.get_retailer_price(retailer, product, quantity)
            
            return Response(pricing)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkPricingView(APIView):
    """API view for bulk pricing calculation."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            retailer_id = request.data.get('retailer_id')
            products = request.data.get('products', [])  # List of {'product_id': ..., 'quantity': ...}
            
            if not retailer_id or not products:
                return Response(
                    {'error': 'Retailer ID and products list are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                retailer = Retailer.objects.get(retailer_id=retailer_id)
            except Retailer.DoesNotExist:
                return Response(
                    {'error': 'Retailer not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            product_quantities = []
            for item in products:
                try:
                    product = Product.objects.get(product_id=item['product_id'])
                    quantity = float(item.get('quantity', 1))
                    product_quantities.append((product, quantity))
                except Product.DoesNotExist:
                    continue
            
            pricing_results = PricingService.get_bulk_pricing(retailer, product_quantities)
            
            return Response({
                'retailer': retailer.retailer_name,
                'pricing_results': pricing_results
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExpiryDiscountsView(APIView):
    """API view for expiry discount suggestions."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        days_ahead = int(request.query_params.get('days', 7))
        suggestions = PricingService.get_expiry_discounts(days_ahead)
        
        return Response({
            'discount_suggestions': suggestions,
            'total_suggestions': len(suggestions),
            'days_ahead': days_ahead
        })


class RetailerPricingSummaryView(APIView):
    """API view for retailer pricing summary."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, retailer_id):
        try:
            retailer = Retailer.objects.get(retailer_id=retailer_id)
            summary = PricingService.get_pricing_summary(retailer)
            
            return Response(summary)
            
        except Retailer.DoesNotExist:
            return Response(
                {'error': 'Retailer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
