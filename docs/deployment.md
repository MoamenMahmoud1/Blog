# Free Render Trial + Neon

The active `render.yaml` is intentionally designed for a zero-cost evaluation.
It is useful for testing the blog, but it is not the final production topology.
The complete paid profile remains in `unused/render-paid/render.yaml`.

## Active topology

```text
GitHub main
   │ checks pass
   ▼
Render Blueprint
   ├── Free web service ─────┬── Neon PostgreSQL (pooled, TLS)
   │                         ├── Free Render Key Value cache
   │                         └── ephemeral profile media
   └── Free Key Value cache

Not deployed: Celery worker · Redis broker · persistent disk
```

## Free-tier limitations

- The web service can sleep while idle, so its first request can be slow.
- Uploaded profile images can disappear after a restart or deployment.
- Share-email delivery is unavailable because there is no Celery worker.
- Migrations run when the web service starts instead of in a separate
  pre-deploy phase.
- The free configuration uses one Gunicorn worker with two threads to stay
  within the smaller memory allowance.

Posts, users, comments, tags, and permissions remain persistent because they are
stored in Neon rather than on Render's filesystem.

## 1. Prepare Neon

1. Rotate any credential that has been pasted into a message, log, or issue.
2. Keep the Neon project in AWS `us-east-2` and deploy Render in Ohio so the
   application and database remain in the same geographic region.
3. Copy the **pooled** connection string from Neon's Connect dialog.
4. Confirm it requires TLS and keep it private.

Expected shape:

```text
postgresql://USER:PASSWORD@POOLER_HOST/DATABASE?sslmode=require
```

The active app uses persistent connections with a 60-second maximum age and
connection health checks.

## 2. Push the repository

Push the reviewed `main` branch to GitHub. GitHub Actions checks Python,
templates, Django configuration, migrations, tests, and the production Docker
image before Render automatically deploys it.

## 3. Create the Blueprint

1. Open the Render Dashboard.
2. Choose **New → Blueprint**.
3. Connect the GitHub repository and select `main`.
4. Confirm Render detected the root `render.yaml`.
5. Review that both resources show the free plan before applying.

The Blueprint creates only:

- `django-blog-web`
- `django-blog-cache`

The web start command performs the migration and starts Gunicorn only if the
migration succeeds:

```bash
python manage.py migrate --noinput && \
  exec gunicorn --config gunicorn.conf.py mysite.wsgi:application
```

Static files are collected during the Docker build and served by WhiteNoise
using hashed, compressed filenames.

## 4. Supply the required values

Render generates `DJANGO_SECRET_KEY`. Supply the three values marked
`sync: false` in the Blueprint form:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Rotated Neon pooled URL with `sslmode=require` |
| `ALLOWED_HOSTS` | Public hostname without scheme or path |
| `CSRF_TRUSTED_ORIGINS` | Matching public origin beginning with `https://` |

For the initial Render hostname:

```text
ALLOWED_HOSTS=django-blog-web.onrender.com
CSRF_TRUSTED_ORIGINS=https://django-blog-web.onrender.com
```

Use the hostname Render actually assigns if it differs. Django also appends
Render's `RENDER_EXTERNAL_HOSTNAME` automatically at runtime. Multiple values
are comma-separated.

Never paste secrets into `render.yaml`, source control, screenshots, issues, or
application logs.

## 5. Verify the first deployment

Wait for the Docker build, migration, Gunicorn startup, and readiness check.
Then verify:

```text
✓ /health/live/  returns 200
✓ /health/ready/ returns 200
✓ /blog/ renders over HTTPS
✓ static assets load
✓ signup creates a profile and author permissions
✓ posts persist across a new deployment
✓ search suggestions and progressive loading work
✓ comments can be created
✓ unauthorized /admin/ requests return 404
✓ /blog/feed/ and /sitemap.xml are available
⚠ uploaded images are treated as temporary
⚠ share email reports unavailable while the worker is absent
```

Create the first administrator using a Render Shell if the dashboard exposes
one for the service plan:

```bash
python manage.py createsuperuser
```

If an interactive shell is unavailable on the free plan, create the
administrator locally against the same Neon database, then remove the database
URL from shell history where applicable.

## 6. Add a custom domain later

Add the domain in Render, apply the DNS records it provides, then update
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`. Production always redirects HTTP to
HTTPS. Do not enable HSTS for all subdomains or request preload until every
subdomain is permanently HTTPS-only.

## Upgrade to the paid profile

The archived profile adds:

- a dedicated Celery worker;
- a dedicated Redis broker with a non-evicting persistence policy;
- SMTP configuration;
- a persistent media disk;
- a separate pre-deploy migration command;
- two Gunicorn workers.

When ready to upgrade, review—not blindly copy—the current provider plans and
then promote `unused/render-paid/render.yaml` back to the repository root. Keep
cache and broker separate. For horizontal scaling, use object storage instead
of the attached disk.

## Rollout safety

- Make migrations backward-compatible with the previously deployed code.
- Deploy schema additions before code that depends exclusively on them.
- Separate destructive cleanup from the release that stops using old fields.
- A code rollback does not reverse a database migration.
- Create a Neon restore point or branch before destructive data changes.

## Provider references

- [Render free instances](https://render.com/docs/free)
- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
- [Render Django deployment guide](https://render.com/docs/deploy-django)
- [Neon connection pooling](https://neon.com/docs/connect/connection-pooling)
- [Django deployment checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
