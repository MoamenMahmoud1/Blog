# Render + Neon Deployment

This is the production runbook for the active deployment target. Files under
`unused/vps/` are archived and are not part of these steps.

## Target topology

```text
GitHub main
   │ checks pass
   ▼
Render Blueprint
   ├── Web service ───────┬── Neon PostgreSQL (pooled, TLS)
   │                      ├── Redis cache
   │                      └── persistent media disk
   ├── Celery worker ─────┬── Redis broker
   │                      └── SMTP provider
   ├── Redis cache
   └── Redis broker
```

## 1. Prepare Neon

1. Create the Neon project in the same geographic area as the Render services.
2. Copy the **pooled** PostgreSQL connection string.
3. Confirm the host identifies the pooler and the URL requires TLS.
4. Keep the value private; it becomes Render's `DATABASE_URL` secret.

Expected shape:

```text
postgresql://USER:PASSWORD@POOLER_HOST/DATABASE?sslmode=require
```

The application enables persistent connections and connection health checks.
The default `DB_CONN_MAX_AGE` is 60 seconds.

## 2. Push the repository

Push the reviewed branch to GitHub. CI must pass its lint, Django check,
migration check, tests, and Docker build before Render automatically deploys
`main`.

## 3. Create the Render Blueprint

In Render, create a Blueprint from the repository's `render.yaml`. It defines:

- `django-blog-web`
- `django-blog-worker`
- `django-blog-cache`
- `django-blog-broker`
- the profile-media disk attached to the web service

The web image runs Gunicorn. Before each deployment becomes live, Render runs:

```bash
python manage.py migrate --noinput
```

Static files are collected while building the Docker image and served by
WhiteNoise using hashed, compressed filenames.

## 4. Set required secrets

Values marked `sync: false` must be supplied in the Render dashboard.

| Variable | Example / rule |
| --- | --- |
| `DATABASE_URL` | Neon pooled URL with `sslmode=require` |
| `ALLOWED_HOSTS` | `blog.example.com` without scheme or path |
| `CSRF_TRUSTED_ORIGINS` | `https://blog.example.com` with scheme |
| `EMAIL_HOST_USER` | SMTP account username |
| `EMAIL_HOST_PASSWORD` | SMTP app password or provider secret |
| `DEFAULT_FROM_EMAIL` | `My Blog <noreply@example.com>` |

Render generates `DJANGO_SECRET_KEY`. The worker receives the same value from
the web service. Do not paste secrets into `render.yaml`, `.env`, screenshots,
issues, or logs.

Multiple hosts and trusted origins are comma-separated:

```text
ALLOWED_HOSTS=blog.example.com,www.blog.example.com
CSRF_TRUSTED_ORIGINS=https://blog.example.com,https://www.blog.example.com
```

Render's generated hostname is added automatically through
`RENDER_EXTERNAL_HOSTNAME`.

## 5. Deploy and verify

Watch the first deployment until the migration and health check complete. Then
verify:

```text
✓ /health/live/  returns 200
✓ /health/ready/ returns 200
✓ /blog/ renders over HTTPS
✓ /static/... assets load with hashed filenames
✓ signup creates an author account and profile
✓ search returns ranked results and loads another batch
✓ a share request reaches the Celery worker and SMTP provider
✓ unauthorized /admin/ requests return 404
✓ /blog/feed/ and /sitemap.xml are valid
```

Create the first administrator from a Render Shell:

```bash
python manage.py createsuperuser
```

## 6. Attach the custom domain

Add the domain in Render, apply the DNS records Render provides, then update
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`. Production always redirects HTTP to
HTTPS. Do not enable HSTS for every subdomain or request preload until every
subdomain is permanently HTTPS-only.

## Pre-deployment verification

Use production-like values without committing them:

```bash
DJANGO_SETTINGS_MODULE=mysite.settings_production \
DJANGO_DEBUG=False \
DJANGO_SECRET_KEY='replace-with-a-random-value-of-at-least-50-characters' \
ALLOWED_HOSTS='blog.example.com' \
CSRF_TRUSTED_ORIGINS='https://blog.example.com' \
DATABASE_URL='postgresql://user:password@host/database?sslmode=require' \
CACHE_URL='redis://host:6379/1' \
CELERY_BROKER_URL='redis://host:6379/0' \
.venv/bin/python src/manage.py check --deploy \
  --settings=mysite.settings_production
```

Run this against disposable or intended infrastructure; the readiness check and
test suite may contact configured services.

## Rollout and rollback

- Database migrations must be backward-compatible with the previously deployed
  application during rollout.
- Deploy schema additions before code that depends exclusively on them.
- Avoid destructive migrations in the same release that stops reading the old
  schema.
- Roll back the Render deploy if application health fails.
- A code rollback does not automatically reverse a database migration.
- Take a Neon restore point or branch before destructive data changes.

## Scaling note

The attached Render disk is appropriate for the current single web instance,
but it prevents horizontal web scaling and zero-downtime disk movement. Move
profile media to object storage before adding web instances. PostgreSQL, cache,
broker, and static files are already external or immutable.

## Provider references

- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
- [Render Django deployment guide](https://render.com/docs/deploy-django)
- [Neon connection pooling](https://neon.com/docs/connect/connection-pooling)
- [Django deployment checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
