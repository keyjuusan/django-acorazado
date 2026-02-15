from .base import * # noqa

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# --- SETTINGS DE DESARROLLO ---

DEBUG = True # Mantener en True para ver errores detallados

# Permitir que el frontend (Next.js) acceda
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# Confianza para CSRF (importante para peticiones POST/PUT)
CSRF_TRUSTED_ORIGINS = ["http://localhost:3000"]

# Cookies en desarrollo (HTTP normal)
AUTH_COOKIE_SECURE = False  # False porque localhost no suele usar HTTPS
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Localización al español (opcional pero recomendado)
LANGUAGE_CODE = "es-es"
TIME_ZONE = "America/Bogota" # O tu zona horaria

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "desarrollo_local.sqlite3",  #noqa <--- Cambia el nombre aquí
    }
}