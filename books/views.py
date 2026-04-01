from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.conf import settings
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema

from books.models import Book
from books.serializers import BookSerializer
from books.services.exchange_rate import ExchangeRateUnavailable, get_exchange_rate_with_fallback
from books.services.pricing import compute_local_cost_and_selling


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Categoría del libro en formato texto libre (Ej: Ficción, Ciencia, Tecnología).",
                required=True,
            )
        ],
        responses=BookSerializer(many=True), # Mapeo dinámico para activar paginación en la vista
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search_by_category(self, request):
        category = request.query_params.get("category")
        if not category:
            return Response(
                {"detail": "Query param 'category' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset().filter(category__iexact=category)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="threshold",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Límite máximo de stock bajo (por defecto: 10).",
                required=False,
            )
        ],
        responses=BookSerializer(many=True), # Mapeo dinámico para activar paginación en la vista
    )
    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        threshold = request.query_params.get("threshold", "10")
        try:
            threshold_value = int(threshold)
            if threshold_value < 0:
                raise ValueError
        except ValueError:
            return Response(
                {"detail": "Query param 'threshold' must be a non-negative integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset().filter(stock_quantity__lt=threshold_value)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="calculate-price")
    def calculate_price(self, request, pk=None):
        # 1. Validar que el libro exista sin bloquear la fila aun
        book = self.get_object()
        currency = settings.LOCAL_CURRENCY

        # 2. Llamada a API de Divisas (fuera de la transacción para no bloquear conexiones a BD)
        try:
            exchange_rate, rate_source = get_exchange_rate_with_fallback(currency)
        except ExchangeRateUnavailable as exc:
            return Response(
                {
                    "detail": str(exc),
                    "code": "exchange_rate_unavailable",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        calculation_ts = timezone.now()

        # 3. Transacción: bloqueamos registro, recalculamos costo y actualizamos
        with transaction.atomic():
            locked_book = self.get_queryset().select_for_update().get(pk=book.pk)
            
            cost_local, selling_price_local = compute_local_cost_and_selling(
                locked_book.cost_usd,
                exchange_rate,
            )
            
            locked_book.selling_price_local = selling_price_local
            locked_book.save(update_fields=["selling_price_local", "updated_at"])

        return Response(
            {
                "book_id": locked_book.id,
                "cost_usd": locked_book.cost_usd,
                "exchange_rate": exchange_rate,
                "cost_local": cost_local,
                "margin_percentage": settings.PRICING_MARGIN_PERCENTAGE,
                "selling_price_local": selling_price_local,
                "currency": currency,
                "calculation_timestamp": calculation_ts,
                "rate_source": rate_source,
            },
            status=status.HTTP_200_OK,
        )
