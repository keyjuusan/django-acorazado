# Django Acorazado

Backend API REST construido con Django + Django REST Framework. Es la base de seguridad para el proyecto.

## Stack

- **Django 6.0** - Framework web Python
- **Django REST Framework** - API REST
- **Simple JWT** - Autenticación JWT con cookies http-only
- **SQLite** - Base de datos (desarrollo)
- **drf-spectacular** - Documentación/openapi
- **django-cors-headers** - CORS configurado
- **django-filter** - Filtros para endpoints

## Requisitos

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (gestor de paquetes)

## Instalación

```bash
# 1. Crear entorno virtual
uv venv
source .venv/bin/activate

# 2. Instalar dependencias
uv sync

# 3. Migraciones
python manage.py migrate

# 4. Crear superuser (opcional)
python manage.py createsuperuser

# 5. Iniciar servidor
python manage.py runserver
```

Servidor disponible en `http://localhost:8000`

## Estructura

```
├── backend/               # Configuración Django
│   ├── settings/          # Config por entorno
│   └── urls.py
├── core/                  # Auth JWT (login, logout, refresh)
├── usuarios/              # CRUD User/Group
├── manage.py
└── pyproject.toml
```

## Autenticación JWT

**Arquitectura de seguridad:**

- Access token: 60 minutos (en cookie http-only)
- Refresh token: 7 días (en cookie http-only)
- CSRF token: generado en login, enviado en headers

**Flow:**

1. `POST /api/auth/login/` → Recibes cookies + CSRF token
2. Llamadas autenticadas → Header `X-CSRFToken: <valor>`
3. `POST /api/auth/logout/` → Blacklist refresh token + borra cookies

**Cookies:**

- `access_token` - http-only, no accesible desde JS
- `refresh_token` - http-only
- `csrftoken` - disponible para leer desde JS (necesario para agregar en headers)

## Configuración

### Entornos

| Archivo | Uso |
|---------|-----|
| `settings/base.py` | Configuración base |
| `settings/local.py` | Desarrollo local |
| `settings/produccion.py` | Producción |

### CORS

Configurado para `http://localhost:3000` (Next.js frontend).

### Producción

Antes de deployar:
- `DEBUG = False`
- `AUTH_COOKIE_SECURE = True`
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- Cambiar `SECRET_KEY`
- Configurar `ALLOWED_HOSTS`

## Endpoints

| Método | Endpoint | Descripción |
|--------|---------|-------------|
| POST | `/api/auth/login/` | Obtener tokens JWT |
| POST | `/api/auth/logout/` | Cerrar sesión |
| POST | `/api/token/refresh/` | Refrescar access token |
| GET/POST | `/api/usuarios/` | Listar / crear usuarios |
| GET/PUT/PATCH/DELETE | `/api/usuarios/{id}/` | Detalle / editar / eliminar usuario |
| GET/POST | `/api/grupos/` | Listar / crear grupos |
| GET/PUT/PATCH/DELETE | `/api/grupos/{id}/` | Detalle / editar / eliminar grupo |
| GET | `/api/docs` | Documentación API (Swagger UI) |
| GET | `/api/schema/` | Schema OpenAPI |

Admin: `/admin/`

## Documentación API

Swagger UI disponible en `/api/docs`

Schema OpenAPI en `/api/schema/`

## Desarrollo

```bash
# apply migrations
python manage.py makemigrations
python manage.py migrate

# crear app nueva
python manage.py startapp <nombre_app>

# shell Django
python manage.py shell
```
