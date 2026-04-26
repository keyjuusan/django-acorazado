# Backend - Proyecto Ski

Backend API REST construido con Django + Django REST Framework. Es la base de seguridad para el proyecto.

## Stack

- **Django 6.0** - Framework web Python
- **Django REST Framework** - API REST
- **Simple JWT** - Autenticación JWT con cookies http-only
- **SQLite** - Base de datos (desarrollo)
- **drf-spectacular** - Documentación/openapi
- **django-cors-headers** - CORS configurado

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
backend/
├── backend/           # Configuración Django
│   ├── settings/      # Config por entorno
│   └── urls.py
├── usuarios/         # CRUD User/Group
├── sesion/            # Auth JWT
├── manage.py
└── pyproject.toml
```

## Autenticación JWT

**Arquitectura de seguridad:**

- Access token: 60 minutos (en cookie http-only)
- Refresh token: 7 días (en cookie http-only)
- CSRF token: generado en login, enviado en headers

**Flow:**

1. `POST /auth/login/` → Recibes cookies + CSRF token
2. Llamadas autenticadas → Header `X-CSRFToken: <valor>`
3. `POST /auth/logout/` → Blacklist refresh token + borra cookies

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
- Cambiar `SECRET_KEY`
- Configurar `ALLOWED_HOSTS`

## Endpoints

| Método | Endpoint | Descripción |
|--------|---------|-------------|
| POST | `/auth/login/` | Obtener tokens JWT |
| POST | `/auth/logout/` | Cerrar sesión |
| POST | `/api/token/refresh/` | Refrescar access token |
| GET | `/api/users/` | Listar usuarios |
| POST | `/api/users/` | Crear usuario |
| GET | `/api/groups/` | Listar grupos |
| GET | `/api/docs/` | Documentación API |

Admin: `/admin/`

## Documentación API

Swagger UI disponible en `/api/docs/`

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
