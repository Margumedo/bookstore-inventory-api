"""
Modelo de inventario de libros.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from books.validators import validate_isbn


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(
        max_length=13,
        unique=True,
        validators=[validate_isbn],
        help_text='ISBN-10 or ISBN-13. Separators are accepted and stripped before storage.',
    )
    cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'), message='cost_usd must be greater than 0.')],
    )
    selling_price_local = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=100, db_index=True)
    supplier_country = models.CharField(
        max_length=2,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z]{2}$',
                message='supplier_country must be a two-letter country code.',
            )
        ],
        help_text='Two-letter country code, e.g. ES.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cost_usd__gt=0),
                name='book_cost_usd_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(stock_quantity__gte=0),
                name='book_stock_non_negative',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.title} ({self.isbn})'

    def save(self, *args, **kwargs):
        if self.isbn:
            self.isbn = validate_isbn(self.isbn)
        if self.supplier_country:
            self.supplier_country = self.supplier_country.upper()
        super().save(*args, **kwargs)
