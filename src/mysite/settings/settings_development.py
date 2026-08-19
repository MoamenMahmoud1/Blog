"""Settings for local development through ``manage.py``.

Production continues to use ``mysite.settings_production`` explicitly.
"""

import os

# Set this before importing the shared settings so their development-safe
# defaults are selected even when no local .env file exists.
os.environ.setdefault("DJANGO_DEBUG", "True")

from .settings import *  # noqa: E402, F403, F405

ALLOWED_HOSTS = list(
    dict.fromkeys([*ALLOWED_HOSTS, "localhost", "127.0.0.1", "[::1]"])  # noqa: F405
)
CSRF_TRUSTED_ORIGINS = list(
    dict.fromkeys(
        [
            *CSRF_TRUSTED_ORIGINS,  # noqa: F405
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    )
)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "django-blog-development",
    }
}
