FROM python:3.14.6-slim-trixie AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY requirements.txt ./

RUN python -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --upgrade pip \
    && /opt/venv/bin/python -m pip install --requirement requirements.txt


FROM python:3.14.6-slim-trixie AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}"

RUN groupadd --system django \
    && useradd \
        --system \
        --gid django \
        --home-dir /app \
        --shell /usr/sbin/nologin \
        django

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=django:django src/ ./
COPY --chown=django:django docker/django/gunicorn.conf.py ./gunicorn.conf.py

RUN mkdir -p /app/staticfiles /app/media /app/.gunicorn \
    && chown -R django:django \
        /app/staticfiles \
        /app/media \
        /app/.gunicorn

USER django

RUN DJANGO_SETTINGS_MODULE=mysite.settings_production \
    DJANGO_DEBUG=False \
    DJANGO_SECRET_KEY=build-only-secret-key-with-more-than-fifty-random-characters-2026 \
    ALLOWED_HOSTS=build.invalid \
    CSRF_TRUSTED_ORIGINS=https://build.invalid \
    DATABASE_URL=postgresql://build:build@localhost:5432/build \
    STATIC_ROOT=/app/staticfiles \
    MEDIA_ROOT=/app/media \
    python manage.py collectstatic --noinput --clear

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "mysite.wsgi:application"]
