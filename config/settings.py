"""Configuración única, controlada por variables de entorno (ver .env.example)."""

from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env("DEBUG")

# En producción la SECRET_KEY es obligatoria; en desarrollo hay un valor inseguro por defecto.
SECRET_KEY = env(
    "SECRET_KEY", default="dev-only-insecure-key-change-me-0123456789" if DEBUG else environ.Env.NOTSET
)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Render expone el hostname público en esta variable.
_render_host = env("RENDER_EXTERNAL_HOSTNAME", default="")
if _render_host:
    ALLOWED_HOSTS.append(_render_host)
    CSRF_TRUSTED_ORIGINS.append(f"https://{_render_host}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "apps.accounts",
    "apps.tickets",
    "apps.knowledge",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# SQLite por defecto para desarrollo; en producción usar DATABASE_URL de PostgreSQL.
DATABASES = {"default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # JWT primero: así una petición sin credenciales responde 401 (con WWW-Authenticate) y no 403.
        # JWT sirve a clientes externos (curl, apps móviles, scripts).
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # SessionAuthentication: la usa el frontend (mismo origen, cookie + CSRF).
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "apps.tickets.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.tickets.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "auth": env("THROTTLE_AUTH", default="30/min"),
        "assistant": env("THROTTLE_ASSISTANT", default="20/min"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Whodesk API",
    "DESCRIPTION": "API de tickets de soporte con asistente de IA.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# --- Asistente de IA ------------------------------------------------------------
# LLM_PROVIDER: "none" (por defecto, sin costo: respuestas extractivas de la base de
# conocimiento), "anthropic" o "openai" (cualquier API compatible con chat completions).
LLM_PROVIDER = env("LLM_PROVIDER", default="none")
LLM_API_KEY = env("LLM_API_KEY", default="")
LLM_MODEL = env("LLM_MODEL", default="")
LLM_BASE_URL = env("LLM_BASE_URL", default="")
LLM_TIMEOUT = env.float("LLM_TIMEOUT", default=30.0)
LLM_MAX_TOKENS = env.int("LLM_MAX_TOKENS", default=500)
# Tope diario de consultas con LLM por usuario (protege costos de una demo pública).
ASSISTANT_DAILY_LIMIT = env.int("ASSISTANT_DAILY_LIMIT", default=100)
# Umbral de abstención (puntaje BM25). Calibrado con `manage.py eval_rag --sweep`.
ASSISTANT_MIN_SCORE = env.float("ASSISTANT_MIN_SCORE", default=2.5)

if LLM_PROVIDER not in {"none", "anthropic", "openai"}:
    raise ImproperlyConfigured("LLM_PROVIDER debe ser none, anthropic u openai")

# --- Seguridad en producción --------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # COOKIE_SECURE=False solo para probar en local por http (p. ej. docker compose).
    SESSION_COOKIE_SECURE = env.bool("COOKIE_SECURE", default=True)
    CSRF_COOKIE_SECURE = env.bool("COOKIE_SECURE", default=True)
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
    SECURE_REDIRECT_EXEMPT = [r"^api/health/$"]
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"std": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "std"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
