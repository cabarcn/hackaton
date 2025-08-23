from pathlib import Path
import os
from dotenv import load_dotenv

# ─────────────────────────  .env  ─────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def env_bool(name: str, default=False) -> bool:
    return str(os.getenv(name, str(default))).lower() in ("1", "true", "yes", "y", "on")

def env_csv(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]
# ──────────────────────────────────────────────────────────

# Quick-start development settings - unsuitable for production
# https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# ───────────────────── Seguridad básica ───────────────────
DEBUG = env_bool("DEBUG", True)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-key")
if not DEBUG and SECRET_KEY == "dev-only-key":
    raise RuntimeError("Configura SECRET_KEY en producción (variable de entorno SECRET_KEY)")

ALLOWED_HOSTS = env_csv("ALLOWED_HOSTS", "127.0.0.1,localhost")
CSRF_TRUSTED_ORIGINS = env_csv(
    "CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:8000,http://localhost:8000"
)

# ─────────────────── Definición de apps ───────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sitio.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "core" / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sitio.wsgi.application'

# ──────────────────────── Base de datos ───────────────────
# Puedes cambiar a Postgres con DATABASE_URL si quieres más adelante.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ───────────────── Validadores de password ────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─────────────────── Internacionalización ─────────────────
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# ─────────────────── Archivos estáticos/media ─────────────
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "core" / "static"] if (BASE_DIR / "core" / "static").exists() else []

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────── Autenticación (rutas) ────────────────
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/proposito/'
LOGOUT_REDIRECT_URL = '/login/'

# ───────────────────────── Email ──────────────────────────
# En DEV guarda correos en disco. Cambia a SMTP cuando quieras enviar realmente.
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.filebased.EmailBackend")
EMAIL_FILE_PATH = BASE_DIR / "outbox"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@licitaciones.local")

# ─────────────────── OpenAI (referencias) ─────────────────
# La API key NO se guarda aquí. Tu servicio leerá OPENAI_API_KEY del .env.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
