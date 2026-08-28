# Bookstore Inventory API

API REST para gestion de inventario de librerias con validacion de precios en tiempo real.

## Quick Review

Produccion (Render + PostgreSQL):

- **API:** https://bookstore-inventory-api-phzz.onrender.com/api/v1/books/
- **Swagger:** https://bookstore-inventory-api-phzz.onrender.com/api/docs/
- **OpenAPI:** https://bookstore-inventory-api-phzz.onrender.com/api/schema/
- **Health:** https://bookstore-inventory-api-phzz.onrender.com/health/
- **Repo:** https://github.com/Margumedo/bookstore-inventory-api

Local en un comando: `docker compose up --build` → `http://localhost:8000/api/docs/`

Postman: importar `postman/Bookstore_Inventory_API.postman_collection.json` y Send/Runner. Apunta a produccion; no hace falta configurar URL.

[![Tests](https://github.com/Margumedo/bookstore-inventory-api/actions/workflows/tests.yml/badge.svg)](https://github.com/Margumedo/bookstore-inventory-api/actions/workflows/tests.yml)

## Decisiones

- Prefijo `/api/v1/` y barra final (convencion Django/DRF).
- ISBN: se quitan guiones y espacios; deben quedar exactamente 10 o 13 digitos.
- Moneda local: `LOCAL_CURRENCY` (por defecto `EUR`).
- Precio sugerido: `cost_usd × tasa × 1.40`, redondeo half-up por paso (`15.99 × 0.85 = 13.59`, luego `19.03`).
- Si la API de tasas falla: se usa `DEFAULT_EXCHANGE_RATE` y se responde **200** con `rate_source: fallback`. **503** solo si tampoco hay fallback usable.
- `rate_source`: `live` | `cache` | `fallback`.

## Stack

- Python 3.13
- Django 5.2.17 + Django REST Framework 3.18.0
- PostgreSQL 16
- Docker

## Requisitos previos

- Docker y Docker Compose (camino recomendado)
- Python 3.12+ (si se corre sin Docker)
- Git
- Postman (opcional, para la coleccion de entrega)

## Ejecucion con Docker

```bash
git clone https://github.com/Margumedo/bookstore-inventory-api.git
cd bookstore-inventory-api
cp .env.example .env
docker compose up --build
```

Compose aplica migraciones al arrancar.

- API: `http://localhost:8000/api/v1/`
- Swagger: `http://localhost:8000/api/docs/`
- Health: `http://localhost:8000/health/`

## Ejecucion local (sin Docker)

Hace falta PostgreSQL accesible con la `DATABASE_URL` de `.env.example`.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Para correr tests: `pip install -r requirements-dev.txt && pytest`

## Ejemplos de uso

Crear un libro:

```bash
curl -X POST http://localhost:8000/api/v1/books/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "El Quijote",
    "author": "Miguel de Cervantes",
    "isbn": "978-84-376-0494-7",
    "cost_usd": "15.99",
    "stock_quantity": 25,
    "category": "Literatura Clasica",
    "supplier_country": "ES"
  }'
```

Calcular precio de venta sugerido (cuerpo vacio):

```bash
curl -X POST http://localhost:8000/api/v1/books/1/calculate-price/
```

Respuesta esperada (la tasa viva cambia; el ejemplo del enunciado usa `0.85`):

```json
{
  "book_id": 1,
  "cost_usd": "15.99",
  "exchange_rate": "0.85000000",
  "cost_local": "13.59",
  "margin_percentage": 40,
  "selling_price_local": "19.03",
  "currency": "EUR",
  "rate_source": "live",
  "calculation_timestamp": "2025-01-15T10:30:00Z"
}
```

## Endpoints

Las rutas usan barra final. Prefijo canonico: `/api/v1/`.

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/api/v1/books/` | Crear un libro |
| GET | `/api/v1/books/` | Listar libros (paginado) |
| GET | `/api/v1/books/{id}/` | Obtener libro por ID |
| PUT | `/api/v1/books/{id}/` | Reemplazar libro (recurso completo) |
| PATCH | `/api/v1/books/{id}/` | Actualizacion parcial |
| DELETE | `/api/v1/books/{id}/` | Eliminar libro |
| GET | `/api/v1/books/?category={category}` | Filtrar por categoria |
| GET | `/api/v1/books/search/?category={category}` | Buscar por categoria |
| GET | `/api/v1/books/low-stock/?threshold=10` | Libros con stock bajo |
| POST | `/api/v1/books/{id}/calculate-price/` | Calcular precio de venta sugerido |
| GET | `/health/` | Health check |
| GET | `/api/docs/` | Swagger UI |
| GET | `/api/schema/` | OpenAPI schema |
| GET | `/` | Redirige a Swagger |

## Postman

Importar `postman/Bookstore_Inventory_API.postman_collection.json`. `{{base_url}}` ya apunta a produccion. Send o Runner pegan a Render sin configurar nada.

`book_id` va en Params (path) e `isbn` en el body. `category` y `threshold` van en query. Se editan en cada peticion.

Si se corre la coleccion **en orden**, el POST de creacion rellena el `book_id` de las peticiones siguientes durante esa corrida.

## Variables de entorno

Ver `.env.example`. Las principales:

| Variable | Uso |
|----------|-----|
| `DJANGO_SECRET_KEY` | Clave de Django |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos |
| `DATABASE_URL` | PostgreSQL |
| `LOCAL_CURRENCY` | Moneda del precio sugerido (default `EUR`) |
| `DEFAULT_EXCHANGE_RATE` | Fallback si falla la API de tasas |
| `PROFIT_MARGIN_PERCENTAGE` | Margen (default `40`) |
| `EXCHANGE_RATE_API_URL` | API de tasas USD |
| `EXCHANGE_RATE_TIMEOUT_SECONDS` | Timeout HTTP |
| `EXCHANGE_RATE_CACHE_SECONDS` | Cache locmem (~10 min) |

En produccion ademas: `DJANGO_SETTINGS_MODULE=bookstore.settings.production`.

## Tests

Los tests usan PostgreSQL, no SQLite. En cada push, GitHub Actions levanta un Postgres temporal (no el de Render) y corre `pytest`.

En local hace falta Postgres accesible con la `DATABASE_URL` de `.env.example` (por ejemplo `docker compose up db -d`):

```bash
pip install -r requirements-dev.txt
pytest
```

Los tests de tasas mockean `requests.get`; no llaman a internet.
