# Web del Aula de Cultura ETSII

Repositorio que alberga la web del Aula de Cultura de la ETSII.
<img alt="Aula de cultura" align="right" src="imagenes/image.png" width="15%" />
Estructura principal:
- `backend/`: Proyecto Django con las apps `catalog`, `news`, `rentals` y `users`.
- `frontend/`: Código del frontend (single-page app).

## Cómo ejecutar (desarrollo):
1. Crear un fichero `.env` en `backend/` con las variables necesarias (p. ej. `DJANGO_SECRET_KEY`, `DATABASE_*`, `DEBUG`).
2. Instalar dependencias del backend (uv) y del frontend según corresponda.
3. Ejecutar migraciones y levantar el servidor Django:

```sh
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

## Gestionar dependencias (backend)

Desde la carpeta `backend` usamos la herramienta `uv` para gestionar dependencias. A continuación ejemplos y buenas prácticas:

- Añadir una dependencia (ejemplo con versión explícita):

```sh
cd backend
uv add django
```

- Eliminar una dependencia:

```sh
cd backend
uv remove django
```




