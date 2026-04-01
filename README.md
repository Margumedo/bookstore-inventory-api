# Nextep - Bookstore Inventory API 📚

Esta es la solución a la prueba técnica para el rol de **Backend Developer**. El proyecto es una API REST madura, segura y transaccional para gestionar el inventario de una cadena de librerías.

---

## 🚀 Características Principales (Over-Delivery)

1. **Gestión de Concurrencia (Race Conditions):** El endpoint de cálculo de precio externo utiliza bloqueos conservadores en la base de datos (`select_for_update()`). La petición a la API de Divisas se separa cuidadosamente del bloque de transacción local, evitando retardos o colapsos si múltiples transacciones de ventas suceden a la vez.
2. **Robustez de Validaciones:** La validación de unicidad de ISBN se maneja manualmente en la capa de serialización para devolver un amistoso `HTTP 400 Bad Request` al registrar libros duplicados, erradicando los temidos errores silenciosos `HTTP 500`. 
3. **Resiliencia Externa (Fallback System):** Si la *Exchange Rate API* cae por tiempos de espera o errores internos (Ej. 503), el sistema utiliza una caché local o en su defecto un valor fallback (`DEFAULT_EXCHANGE_RATE`) por variable de entorno, asegurando que la API principal **jamás** se detenga.
4. **Scraping Automatizado del BCV:** Se incluye un "Comando Raro" (Management Command) oficial: `python manage.py update_bcv_rate`. Este módulo extrae el DOM de la página oficial del *Banco Central de Venezuela* para parsear la tasa vigente diaria y la asienta en caché automáticamente. Ideal para usarse como una métrica en tareas CRON.
5. **Documentación Auto-generada (Swagger):** Incluye *drf-spectacular* para inyectar un esquema OpenAPI robusto, donde el evaluador podrá testear fácilmente gracias a esquemas paramétricos paginados.

---

## 🐳 Despliegue Local con Docker (Recomendado)

El proyecto viene completamente orquestado con Docker y Docker Compose, configurado para conectar la API desarrollada en Django transparente a un contenedor de **PostgreSQL 16**.

### Requisitos
- **Docker** y **Docker Compose** instalados.

### Instrucciones de Ejecución

1. Clonar el repositorio y entrar a la estructura principal:
   ```bash
   git clone https://github.com/Margumedo/bookstore-inventory-api.git
   cd bookstore-inventory-api
   ```
2. Levantar la infraestructura. El servicio `web` automáticamente se encargará de ejecutar las migraciones (`manage.py migrate`) e iniciar el servidor:
   ```bash
   docker compose up --build
   ```
   *(Si deseas correrlo en segundo plano añade el flag `-d`)*.

La API quedará expuesta en `http://127.0.0.1:8000`.

---

## 🗂 Uso de Endpoints / Postman

Dentro de la raíz del proyecto encontrarás el archivo de colección exportado:
**`Nextep_Bookstore_API.postman_collection.json`**

Importa este archivo en Postman y tendrás disponibles todos los Endpoints CRUD y Bonus funcionales:
- **POST `/api/books/`** (Creación dinámica de un libro, valida el formato del ISBN sin guiones obligatorios).
- **POST `/api/books/{id}/calculate-price/`** (Genera una consulta al tipo de cambio en tiempo real y asigna 40% de margen de ganancia).
- **GET `/api/books/low-stock/`**
- **GET `/api/books/search/`**

### Documentación Visual
Para probar los endpoints desde tu navegador web y leer visualmente las especificaciones, ingresa a la siguiente ruta cuando el Contenedor Docker esté corriendo:
- **Swagger UI:** [http://127.0.0.1:8000/api/docs/swagger/](http://127.0.0.1:8000/api/docs/swagger/)

---

## 🛠 Entorno de Pruebas Unitarias

La suite de tests completa verifica escenarios como ISBN duplicados, rechazo de longitudes erróneas de ISBN, y la validez transaccional del Fallback en distintos ambientes:
```bash
docker compose exec web python manage.py test
```

*Hecho por Maicol Argumedo para Nextep Innovation.*
