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

---

## Frontend (Angular)

Proyecto generado con [Angular CLI](https://github.com/angular/angular-cli) versión 21.2.31. Todos los comandos se ejecutan desde `frontend/`.

### Servidor de desarrollo

```sh
ng serve
```

Una vez iniciado, abre `http://localhost:4200/`. La aplicación se recarga automáticamente al modificar cualquier archivo fuente.

### Generación de código (scaffolding)

```sh
ng generate component nombre-del-componente
```

Para ver la lista completa de esquemas (`components`, `directives`, `pipes`, etc.):

```sh
ng generate --help
```

### Compilación

```sh
ng build
```

Compila el proyecto y guarda los artefactos en `dist/`. Por defecto, la compilación de producción está optimizada para rendimiento y velocidad.

### Tests unitarios

Se usa [Vitest](https://vitest.dev/) como ejecutor de tests:

```sh
ng test
```

### Tests end-to-end

```sh
ng e2e
```

Angular CLI no incluye ningún framework e2e por defecto; puedes elegir el que mejor se adapte.

### Recursos adicionales

Más información en la [referencia de Angular CLI](https://angular.dev/tools/cli).
