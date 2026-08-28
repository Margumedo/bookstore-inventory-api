"""
Serializers del recurso Book.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from books.models import Book
from books.validators import ISBN_DUPLICATE_MESSAGE, validate_isbn


class BookSerializer(serializers.ModelSerializer):
    # El ISBN persistido tiene 13 caracteres; el input puede traer guiones o espacios.
    isbn = serializers.CharField(max_length=32)

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'isbn',
            'cost_usd',
            'selling_price_local',
            'stock_quantity',
            'category',
            'supplier_country',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'selling_price_local']

    def validate_isbn(self, value: str) -> str:
        try:
            normalized = validate_isbn(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

        queryset = Book.objects.filter(isbn=normalized)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(ISBN_DUPLICATE_MESSAGE)
        return normalized

    def validate_cost_usd(self, value: Decimal) -> Decimal:
        if value is None or value <= 0:
            raise serializers.ValidationError('cost_usd debe ser mayor que 0.')
        return value

    def validate_stock_quantity(self, value: int) -> int:
        if value is None or value < 0:
            raise serializers.ValidationError('stock_quantity debe ser mayor o igual a 0.')
        return value

    def validate_supplier_country(self, value: str) -> str:
        normalized = str(value).strip().upper() if value is not None else ''
        if len(normalized) != 2 or not normalized.isalpha():
            raise serializers.ValidationError(
                'supplier_country debe ser un codigo de pais de dos letras.'
            )
        return normalized


class PriceCalculationSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    cost_usd = serializers.DecimalField(max_digits=10, decimal_places=2)
    exchange_rate = serializers.DecimalField(max_digits=18, decimal_places=8)
    cost_local = serializers.DecimalField(max_digits=10, decimal_places=2)
    margin_percentage = serializers.IntegerField()
    selling_price_local = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    rate_source = serializers.CharField()
    calculation_timestamp = serializers.DateTimeField()
