from decimal import Decimal
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book


class BookApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.book = Book.objects.create(
            title="El Quijote",
            author="Miguel de Cervantes",
            isbn="9788437604947",
            cost_usd=Decimal("15.99"),
            stock_quantity=25,
            category="Literatura Clasica",
            supplier_country="es",
        )

    def test_create_book(self):
        payload = {
            "title": "Cien anios de soledad",
            "author": "Gabriel Garcia Marquez",
            "isbn": "9780307474728",
            "cost_usd": "20.00",
            "stock_quantity": 10,
            "category": "Novela",
            "supplier_country": "co",
        }
        response = self.client.post("/api/books/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["supplier_country"], "CO")

    def test_create_book_isbn_with_hyphens_normalizes(self):
        payload = {
            "title": "Otro libro",
            "author": "Autor",
            "isbn": "978-0-306-40615-7",
            "cost_usd": "12.00",
            "stock_quantity": 5,
            "category": "Clasico",
            "supplier_country": "es",
        }
        response = self.client.post("/api/books/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["isbn"], "9780306406157")

    def test_create_book_isbn_wrong_digit_count_rejected(self):
        """99-84-37-04-7 -> 9 digitos; no es un ISBN valido."""
        payload = {
            "title": "Test",
            "author": "Test",
            "isbn": "99-84-37-04-7",
            "cost_usd": "12.00",
            "stock_quantity": 5,
            "category": "X",
            "supplier_country": "es",
        }
        response = self.client.post("/api/books/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("isbn", response.data)

    def test_create_duplicate_isbn_returns_400(self):
        payload = {
            "title": "Otro Libro Copia",
            "author": "Copia",
            "isbn": "978-84-376-0494-7", # This matches self.book's normalized ISBN
            "cost_usd": "12.00",
            "stock_quantity": 5,
            "category": "X",
            "supplier_country": "es",
        }
        response = self.client.post("/api/books/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("isbn", response.data)

    def test_list_books(self):
        response = self.client.get("/api/books/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_book_by_id(self):
        response = self.client.get(f"/api/books/{self.book.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.book.id)

    def test_search_by_category(self):
        response = self.client.get("/api/books/search/?category=Literatura Clasica")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_low_stock(self):
        response = self.client.get("/api/books/low-stock/?threshold=30")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_search_requires_category(self):
        response = self.client.get("/api/books/search/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_low_stock_requires_valid_threshold(self):
        response = self.client.get("/api/books/low-stock/?threshold=-1")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(LOCAL_CURRENCY="EUR", DEFAULT_EXCHANGE_RATE="")
    def test_calculate_price_live_rate(self):
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value.read.return_value = (
            b'{"base":"USD","rates":{"EUR":0.85}}'
        )
        mock_cm.__exit__.return_value = None

        with patch("books.services.exchange_rate.urlopen", return_value=mock_cm):
            response = self.client.post(f"/api/books/{self.book.id}/calculate-price/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rate_source"], "live")
        self.assertEqual(Decimal(str(response.data["cost_local"])), Decimal("13.59"))
        self.assertEqual(Decimal(str(response.data["selling_price_local"])), Decimal("19.03"))
        self.assertEqual(response.data["margin_percentage"], 40)

        self.book.refresh_from_db()
        self.assertEqual(self.book.selling_price_local, Decimal("19.03"))

    @override_settings(LOCAL_CURRENCY="EUR", DEFAULT_EXCHANGE_RATE="")
    def test_calculate_price_uses_cache_when_api_fails(self):
        cache.set("exchange_rate_usd_to_EUR", "0.85")

        with patch(
            "books.services.exchange_rate.urlopen",
            side_effect=URLError("network down"),
        ):
            response = self.client.post(f"/api/books/{self.book.id}/calculate-price/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rate_source"], "cache")

    @override_settings(LOCAL_CURRENCY="EUR", DEFAULT_EXCHANGE_RATE="0.90")
    def test_calculate_price_uses_default_when_api_fails_and_no_cache(self):
        with patch(
            "books.services.exchange_rate.urlopen",
            side_effect=URLError("network down"),
        ):
            response = self.client.post(f"/api/books/{self.book.id}/calculate-price/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rate_source"], "default")

    @override_settings(LOCAL_CURRENCY="EUR", DEFAULT_EXCHANGE_RATE="")
    def test_calculate_price_returns_503_when_no_rate_available(self):
        with patch(
            "books.services.exchange_rate.urlopen",
            side_effect=URLError("network down"),
        ):
            response = self.client.post(f"/api/books/{self.book.id}/calculate-price/")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("detail", response.data)

    def test_calculate_price_not_found(self):
        response = self.client.post("/api/books/999999/calculate-price/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
