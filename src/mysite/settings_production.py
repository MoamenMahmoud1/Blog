from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403, F405

DEBUG = False
validate_production_secret_key(SECRET_KEY)  # noqa: F405

ALLOWED_HOSTS = list(config("ALLOWED_HOSTS", default="", cast=Csv()))
CSRF_TRUSTED_ORIGINS = list(config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv()))
render_hostname = config("RENDER_EXTERNAL_HOSTNAME", default="").strip()
if render_hostname:
    if render_hostname not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(render_hostname)
    render_origin = f"https://{render_hostname}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "Set ALLOWED_HOSTS or deploy through Render with "
        "RENDER_EXTERNAL_HOSTNAME available."
    )
if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured("Set CSRF_TRUSTED_ORIGINS to the public HTTPS origin.")

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_HSTS_SECONDS = 31_536_000
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
X_FRAME_OPTIONS = "DENY"

STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}
WHITENOISE_KEEP_ONLY_HASHED_FILES = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "{asctime} {levelname} {name} "
                "process={process:d} thread={thread:d} {message}"
            ),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": config("DJANGO_LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
