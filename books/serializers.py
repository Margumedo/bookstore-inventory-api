from rest_framework import serializers

from books.models import Book


class BookSerializer(serializers.ModelSerializer):
    # Desactivamos el validador automático Unique de DRF para interceptarlo nosotros mismos 
    # y así evitamos el Internal Server Error (error 500) devolviendo un 400 Bad Request.
    isbn = serializers.CharField(max_length=32, validators=[])

    def validate_isbn(self, value):
        from books.models import normalize_isbn, validate_isbn_digits

        validate_isbn_digits(value)
        normalized = normalize_isbn(value)

        # Verificar unicidad manualmente de forma segura (ignorando el libro actual si es UPDATE)
        qs = Book.objects.filter(isbn=normalized)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
            
        if qs.exists():
            raise serializers.ValidationError("Un libro con este ISBN ya se encuentra registrado.")

        return normalized

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "isbn",
            "cost_usd",
            "selling_price_local",
            "stock_quantity",
            "category",
            "supplier_country",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "selling_price_local", "created_at", "updated_at"]
