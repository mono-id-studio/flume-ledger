# settings.py
from pathlib import Path
from os import getenv
from environ import Env  # type: ignore

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Env ────────────────────────────────────────────────────────────────────────
env = Env(
    # default values
    DEBUG=(bool, False),
    ENVIRONMENT=(str, "development"),
    SECRET_KEY=(str, "unsafe-dev-key"),  # cambia in prod!
    ALLOWED_HOSTS=(list, ["*"]),
    TIME_ZONE=(str, "UTC"),
    # JWT
    JWT_SECRET_KEY=(str, ""),
    JWT_ALGORITHM=(str, "HS256"),
    JWT_EXPIRATION_TIME=(int, 3600),
    JWT_REFRESH_EXPIRATION_TIME=(int, 86400),
    # FLUME
    FLUME_SEED=(str, ""),
)

# Carica .env (puoi cambiare percorso con ENV_PATH)
ENV_PATH = getenv("ENV_PATH", "envs/.env")
env.read_env(BASE_DIR / ENV_PATH)

# ── Core ───────────────────────────────────────────────────────────────────────
DEBUG = env("ENVIRONMENT") == "development"
SECRET_KEY = env("SECRET_KEY")
ENVIRONMENT = env("ENVIRONMENT")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE")
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Apps ───────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "app.wsgi.application"

# ── Database ───────────────────────────────────────────────────────────────────
DATABASES = {"default": env.db(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}

# ── Auth / User ────────────────────────────────────────────────────────────────
# AUTH_USER_MODEL = "app.CustomUser"

# ── Password validators ────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Static ─────────────────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ── I18N ──────────────────────────────────────────────────────────────────────
LOCALE_PATHS = [BASE_DIR / "locale"]

# ── JWT ───────────────────────────────────────────────────────────────────────
JWT_SECRET_KEY = env("JWT_SECRET_KEY")
JWT_ALGORITHM = env("JWT_ALGORITHM")
JWT_EXPIRATION_TIME = env.int("JWT_EXPIRATION_TIME")
JWT_REFRESH_EXPIRATION_TIME = env.int("JWT_REFRESH_EXPIRATION_TIME")

# ── Security flags ─────────────────────────────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# ── MICROSERVICES ───────────────────────────────────────────────────────────────────────

MS_REGION = env("MS_REGION", default="eu-central-1")

# -- REDIS ───────────────────────────────────────────────────────────────────────
REDIS_HOST = env("REDIS_HOST", default="localhost")
REDIS_PORT = env("REDIS_PORT", default="6379")
REDIS_DB = env("REDIS_DB", default=0)
REDIS_PASSWORD = env("REDIS_PASSWORD", default="")
