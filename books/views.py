"""
ViewSet de inventario de libros.
"""

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from books.models import Book
from books.serializers import BookSerializer, PriceCalculationSerializer
from books.services.exchange_rate import ExchangeRateService, ExchangeRateUnavailableError
from books.services.pricing import PricingService
from books.validators import ISBN_DUPLICATE_MESSAGE


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    queryset = Book.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ('list', 'search', 'low_stock'):
            category = self.request.query_params.get('category')
            if category:
                queryset = queryset.filter(category__iexact=category)
        return queryset

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError as exc:
            raise ValidationError(
                {'isbn': [ISBN_DUPLICATE_MESSAGE]}
            ) from exc

    def perform_update(self, serializer):
        try:
            serializer.save()
        except IntegrityError as exc:
            raise ValidationError(
                {'isbn': [ISBN_DUPLICATE_MESSAGE]}
            ) from exc

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """GET /api/v1/books/search/?category=..."""
        category = request.query_params.get('category')
        if not category:
            raise ValidationError({'category': ['El parametro category es obligatorio.']})
        return self.list(request)

    @action(detail=False, methods=['get'], url_path='low-stock')
    def low_stock(self, request):
        """GET /api/v1/books/low-stock/?threshold=10"""
        raw_threshold = request.query_params.get('threshold', 10)
        try:
            threshold = int(raw_threshold)
        except (TypeError, ValueError) as exc:
            raise ValidationError({'threshold': ['threshold debe ser un entero.']}) from exc
        if threshold < 0:
            raise ValidationError({'threshold': ['threshold debe ser mayor o igual a 0.']})

        queryset = self.filter_queryset(self.get_queryset()).filter(
            stock_quantity__lte=threshold
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='calculate-price')
    def calculate_price(self, request, pk=None):
        """POST /api/v1/books/{id}/calculate-price/"""
        book = self.get_object()
        try:
            rate, source = ExchangeRateService().get_rate()
        except ExchangeRateUnavailableError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        calculation = PricingService.calculate(
            cost_usd=book.cost_usd,
            exchange_rate=rate,
            margin_percentage=settings.PROFIT_MARGIN_PERCENTAGE,
            currency=settings.LOCAL_CURRENCY,
        )
        book.selling_price_local = calculation.selling_price_local
        book.save(update_fields=['selling_price_local', 'updated_at'])

        serializer = PriceCalculationSerializer(
            {
                'book_id': book.id,
                'cost_usd': calculation.cost_usd,
                'exchange_rate': calculation.exchange_rate,
                'cost_local': calculation.cost_local,
                'margin_percentage': calculation.margin_percentage,
                'selling_price_local': calculation.selling_price_local,
                'currency': calculation.currency,
                'rate_source': source,
                'calculation_timestamp': timezone.now(),
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
