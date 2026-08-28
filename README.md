# Bookstore Inventory API

API REST para gestion de inventario de librerias con validacion de precios en tiempo real.

## Stack

- Python 3.13
- Django 5.x + Django REST Framework
- PostgreSQL 16
- Docker

## Requisitos previos

- Docker y Docker Compose
- Python 3.12+ (para desarrollo local sin Docker)
- Git

## Ejecucion con Docker

```bash
git clone https://github.com/Margumedo/bookstore-inventory-api.git
cd bookstore-inventory-api
cp .env.example .env
docker compose up --build
```

La API estara disponible en `http://localhost:8000/api/v1/`

Swagger: `http://localhost:8000/api/docs/`

## Ejecucion local (sin Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Endpoints

Las rutas usan barra final (convencion Django/DRF). Prefijo canonico: `/api/v1/`.

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/api/v1/books/` | Crear un libro |
| GET | `/api/v1/books/` | Listar libros (paginado) |
| GET | `/api/v1/books/{id}/` | Obtener libro por ID |
| PUT | `/api/v1/books/{id}/` | Actualizar libro |
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

## Variables de entorno

Ver `.env.example` para la lista completa de variables necesarias.

## Tests

```bash
pytest
```

## Despliegue

La API se encuentra desplegada y funcional en:

- **API:** (pendiente)
- **Swagger:** (pendiente)
