from pathlib import Path

import dj_database_url
from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)

_DEVELOPMENT_SECRET = "django-insecure-development-only-change-me"  # noqa: S105

SECRET_KEY = config(
    "DJANGO_SECRET_KEY",
    default=_DEVELOPMENT_SECRET,
)


def validate_production_secret_key(secret_key):
    if (
        secret_key == _DEVELOPMENT_SECRET
        or secret_key.startswith(("django-insecure-", "replace-"))
        or len(secret_key) < 50
        or len(set(secret_key)) < 5
    ):
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be a unique, random value of at least "
            "50 characters when DJANGO_DEBUG is false."
        )


if not DEBUG:
    validate_production_secret_key(SECRET_KEY)


SECRET_KEY_FALLBACKS = config(
    "DJANGO_SECRET_KEY_FALLBACKS",
    default="",
    cast=Csv(),
)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1,[::1]",
    cast=Csv(),
)

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="",
    cast=Csv(),
)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django_extensions",
    "django.contrib.postgres",
    "taggit",
    "blog.apps.BlogConfig",
    "presentation.apps.PresentationConfig",
    "easy_thumbnails",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "mysite.middleware.HideAdminFromUnauthorizedUsersMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "mysite.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
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


WSGI_APPLICATION = "mysite.wsgi.application"
ASGI_APPLICATION = "mysite.asgi.application"


database_url = config("DATABASE_URL", default="")
db_conn_max_age = config(
    "DB_CONN_MAX_AGE",
    default=60,
    cast=int,
)

if database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=db_conn_max_age,
            conn_health_checks=True,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME"),
            "USER": config("DB_USER"),
            "PASSWORD": config("DB_PASSWORD"),
            "HOST": config("DB_HOST"),
            "PORT": config("DB_PORT", default="5432"),
            "CONN_MAX_AGE": db_conn_max_age,
            "CONN_HEALTH_CHECKS": True,
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.MinimumLengthValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.CommonPasswordValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.NumericPasswordValidator"),
    },
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"

USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"

STATIC_ROOT = Path(
    config(
        "STATIC_ROOT",
        default=BASE_DIR.parent / "staticfiles",
    )
)

MEDIA_URL = "/media/"

MEDIA_ROOT = Path(
    config(
        "MEDIA_ROOT",
        default=BASE_DIR.parent / "media",
    )
)


STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "blog:login"


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config(
            "CACHE_URL",
            default="redis://127.0.0.1:6379/1",
        ),
        "KEY_PREFIX": config(
            "CACHE_KEY_PREFIX",
            default="django-blog",
        ),
        "TIMEOUT": 300,
        "OPTIONS": {
            "socket_connect_timeout": 2,
            "socket_timeout": 2,
        },
    }
}


EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)

EMAIL_HOST = config(
    "EMAIL_HOST",
    default="smtp.gmail.com",
)

EMAIL_HOST_USER = config(
    "EMAIL_HOST_USER",
    default="",
)

EMAIL_HOST_PASSWORD = config(
    "EMAIL_HOST_PASSWORD",
    default="",
)

EMAIL_PORT = config(
    "EMAIL_PORT",
    default=587,
    cast=int,
)

EMAIL_USE_TLS = config(
    "EMAIL_USE_TLS",
    default=True,
    cast=bool,
)

EMAIL_TIMEOUT = config(
    "EMAIL_TIMEOUT",
    default=10,
    cast=int,
)

DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="webmaster@localhost",
)


CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TASK_IGNORE_RESULT = True

CELERY_TASK_ROUTES = {
    "blog.tasks.send_post_share_email": {
        "queue": "email",
    },
}

CELERY_TASK_SOFT_TIME_LIMIT = 20
CELERY_TASK_TIME_LIMIT = 30


SECURE_SSL_REDIRECT = config(
    "SECURE_SSL_REDIRECT",
    default=not DEBUG,
    cast=bool,
)

SESSION_COOKIE_SECURE = config(
    "SESSION_COOKIE_SECURE",
    default=not DEBUG,
    cast=bool,
)

CSRF_COOKIE_SECURE = config(
    "CSRF_COOKIE_SECURE",
    default=not DEBUG,
    cast=bool,
)

SECURE_HSTS_SECONDS = config(
    "SECURE_HSTS_SECONDS",
    default=0 if DEBUG else 31_536_000,
    cast=int,
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=False,
    cast=bool,
)

SECURE_HSTS_PRELOAD = config(
    "SECURE_HSTS_PRELOAD",
    default=False,
    cast=bool,
)

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

X_FRAME_OPTIONS = "DENY"


SECURE_CSP = {
    "default-src": [
        CSP.SELF,
    ],
    "base-uri": [
        CSP.SELF,
    ],
    "connect-src": [
        CSP.SELF,
    ],
    "font-src": [
        CSP.SELF,
        "https://cdn.jsdelivr.net",
    ],
    "form-action": [
        CSP.SELF,
    ],
    "frame-ancestors": [
        CSP.NONE,
    ],
    "img-src": [
        CSP.SELF,
        "data:",
    ],
    "object-src": [
        CSP.NONE,
    ],
    "script-src": [
        CSP.SELF,
        "https://cdn.jsdelivr.net",
    ],
    "style-src": [
        CSP.SELF,
        "https://cdn.jsdelivr.net",
        CSP.UNSAFE_INLINE,
    ],
}


if config(
    "TRUST_X_FORWARDED_PROTO",
    default=False,
    cast=bool,
):
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )


THUMBNAIL_ALIASES = {
    "": {
        "avatar": {
            "size": (150, 150),
            "crop": True,
        },
        "medium": {
            "size": (400, 400),
            "crop": False,
        },
    },
}
