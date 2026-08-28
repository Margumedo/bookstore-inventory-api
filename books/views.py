"""
ViewSet de inventario de libros.
"""

from django.db import IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from books.models import Book
from books.serializers import BookSerializer
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
