from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal


def normalize_isbn(value: str) -> str:
    return "".join(char for char in value if char.isdigit())

def validate_isbn_digits(value: str) -> None:
    """Accepts formatted ISBN (hyphens/spaces); only digit count matters."""
    normalized = normalize_isbn(value)

    if len(normalized) not in (10, 13):
        raise ValidationError(
            "El ISBN debe tener exactamente 10 o 13 dígitos "
            "(guiones y espacios se ignoran)."
        )


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    # max_length permite enviar ISBN con guiones en la API; en clean() se guarda solo digitos (10 u 13).
    isbn = models.CharField(max_length=32, unique=True, validators=[validate_isbn_digits])
    cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    selling_price_local = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField(validators=[MinValueValidator(0)])
    category = models.CharField(max_length=120)
    supplier_country = models.CharField(max_length=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "books"
        ordering = ["-created_at"]

    def clean(self):
        self.isbn = normalize_isbn(self.isbn)
        validate_isbn_digits(self.isbn)
        self.supplier_country = self.supplier_country.upper()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

