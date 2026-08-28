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

La API estara disponible en `http://localhost:8000/api/`

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

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/api/books/` | Crear un libro |
| GET | `/api/books/` | Listar libros (paginado) |
| GET | `/api/books/{id}/` | Obtener libro por ID |
| PUT | `/api/books/{id}/` | Actualizar libro |
| DELETE | `/api/books/{id}/` | Eliminar libro |
| GET | `/api/books/?category={category}` | Filtrar por categoria |
| GET | `/api/books/low-stock/?threshold=10` | Libros con stock bajo |
| POST | `/api/books/{id}/calculate-price/` | Calcular precio de venta sugerido |
| GET | `/api/health/` | Health check |
| GET | `/api/docs/` | Documentacion Swagger |

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
