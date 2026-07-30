# Web del Aula de Cultura ETSII

Repositorio que alberga la web del Aula de Cultura de la ETSII.
<img alt="Aula de cultura" align="right" src="imagenes/image.png" width="15%" />

Estructura principal:
- `backend/`: Proyecto Django (`catalog`, `news`, `rentals`, `users`).
- `frontend/`: Código del frontend.
- `docker-compose.yml`: Servicios de PostgreSQL y Backend.

---

## Ejecución con Docker

### 1. Levantar el entorno por primera vez

```sh
docker compose up --build -d
```

Servicios iniciados:
- **Base de Datos (PostgreSQL)**: puerto `5433` (interno `5432`).
- **Backend (Django + DRF)**: `http://localhost:8000`.

### 2. Migraciones y superusuario

```sh
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

### 3. Levantar el entorno para desarrollo normal

```sh
docker compose up -d
```

### 4. Comandos útiles

- **Ver logs:** `docker compose logs -f backend`
- **Detener servicios:** `docker compose down`
- **Detener y borrar datos:** `docker compose down -v`

---

## Desarrollo local (sin Docker)

```sh
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

### Gestión de dependencias (`uv`)

- **Añadir:** `uv add <paquete>`
- **Eliminar:** `uv remove <paquete>`
