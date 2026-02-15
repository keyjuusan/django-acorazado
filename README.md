# Backend - Proyecto Ski

Backend API REST construido con Django y Django REST Framework.

## Tecnologías

- **Django 6.0.2** - Framework web Python
- **Django REST Framework** - API REST
- **Simple JWT** - Autenticación JWT con cookies
- **SQLite** - Base de datos
- **CORS Headers** - Configuración de CORS para frontend

## Requisitos

- Python 3.13+
- uv (gestor de paquetes)

## Instalación

1. Crear y activar entorno virtual:
```bash
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

2. Instalar dependencias:
```bash
 uv sync
```

3. Ejecutar migraciones:
```bash
python manage.py migrate
```

4. Iniciar servidor:
```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

## Configuración

### Variables de Entorno

El proyecto usa configuración basada en archivos en `backend/settings/`:
- `base.py` - Configuración base
- `local.py` - Desarrollo local
- `produccion.py` - Producción

### CORS

Configurado para permitir solicitudes desde `http://localhost:3000` (Next.js).

### Autenticación JWT

- Token de acceso: 60 minutos
- Token de refresh: 7 días
- Almacenado en cookies HTTP-only

## Estructura del Proyecto

```
backend/
├── backend/           # Configuración Django
│   ├── settings/      # Archivos de configuración
│   ├── urls.py        # URLs principales
│   └── wsgi.py
├── core/              # App principal
├── usuarios/          # App de usuarios y autenticación
├── manage.py
└── pyproject.toml
```

## API Endpoints

- `POST /auth/login/` - Obtener tokens JWT
- `POST /auth/logout/` - Cerrar sesión
- `POST /api/token/refresh/` - Refrescar token
- `GET /admin/` - Panel de administración Django
