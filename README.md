# Django Blog

A production-oriented, server-rendered publishing platform built with Django,
PostgreSQL, Redis, Celery, and progressive enhancement.

```text
  Write → Preview → Publish → Discover → Discuss → Share
```

## ✦ Highlights

- Public post feed with stable, signed cursor pagination and infinite scrolling.
- PostgreSQL full-text search with ranked results and a GIN index.
- Search suggestions and load-more responses rendered as small HTML fragments.
- Draft, scheduled, published, and unpublished post workflows.
- Author dashboard with object-level ownership rules and explicit permissions.
- Safe Markdown rendering through a strict HTML allowlist.
- Comments, tags, related posts, RSS, and an XML sitemap.
- Optional asynchronous email delivery with Celery in the paid deployment profile.
- Redis caching, rate limiting, health checks, and production security headers.
- Responsive UI with page-specific CSS and JavaScript.
- Docker image, Render Blueprint, GitHub Actions, and Dependabot configuration.

## ⌁ System map

```text
                                ┌────────────────────┐
                                │   Browser / Bot    │
                                └─────────┬──────────┘
                                          │ HTTPS
                                ┌─────────▼──────────┐
                                │    Render Edge     │
                                └─────────┬──────────┘
                                          │ proxy
                      ┌───────────────────▼───────────────────┐
                      │       Gunicorn → Django (WSGI)        │
                      │ HTML · search · auth · RSS · sitemap  │
                      └───────┬───────────┬───────────┬───────┘
                              │           │           │
                    ┌─────────▼───┐ ┌─────▼─────┐ ┌──▼───────────┐
                    │ Neon        │ │ Redis     │ │ Ephemeral    │
                    │ PostgreSQL  │ │ cache     │ │ profile media│
                    └─────────────┘ └───────────┘ └──────────────┘
```

For component boundaries and request flows, see
[Architecture](docs/architecture.md).

## ⚙ Quick start

### Requirements

- Python 3.13
- PostgreSQL
- Two Redis-compatible endpoints: one for cache and one for Celery

### Setup

```bash
python -m venv .venv
.venv/bin/python -m pip install --requirement requirements-dev.txt
cp example.env .env
```

Update `.env`, create the PostgreSQL database, and make sure the cache and broker
URLs are reachable. Then run:

```bash
.venv/bin/python src/manage.py migrate
.venv/bin/python src/manage.py createsuperuser
.venv/bin/python src/manage.py runserver
```

Open <http://127.0.0.1:8000/blog/>.

## ◈ Core URLs

| Feature | URL |
| --- | --- |
| Published posts | `/blog/` |
| Search | `/blog/search/` |
| Author dashboard | `/blog/dashboard/` |
| Sign up | `/blog/signup/` |
| RSS feed | `/blog/feed/` |
| Sitemap | `/sitemap.xml` |
| Liveness | `/health/live/` |
| Readiness | `/health/ready/` |

The complete method, authentication, permission, and response reference is in
[Routes](docs/routes.md).

## ⛭ Application structure

```text
.
├── .github/
│   ├── workflows/ci.yml       # quality gates and production image build
│   └── dependabot.yml         # dependency update policy
├── docker/django/
│   ├── Dockerfile             # multi-stage, non-root production image
│   └── gunicorn.conf.py       # process and request lifecycle settings
├── docs/
│   ├── architecture.md        # boundaries, data flows, design decisions
│   ├── deployment.md          # Render + Neon runbook
│   ├── routes.md              # complete HTTP route reference
│   └── security.md            # controls, secrets, operational checklist
├── src/
│   ├── blog/
│   │   ├── views/             # thin HTTP adapters by feature
│   │   ├── selectors.py       # reusable read-side queries
│   │   ├── services.py        # state-changing publication operations
│   │   ├── permissions.py     # permission and ownership rules
│   │   ├── pagination.py      # cursor and no-count batching
│   │   ├── tasks.py           # background jobs
│   │   ├── templates/         # server-rendered UI and fragments
│   │   └── static/blog/       # namespaced, page-scoped frontend assets
│   ├── mysite/                # settings, routing, health, WSGI, ASGI
│   └── manage.py
├── unused/
│   ├── render-paid/           # archived paid Render worker/disk profile
│   └── vps/                   # archived VPS/Compose deployment files
├── render.yaml                # active free Render trial definition
└── requirements*.txt
```

## ✓ Quality checks

Run the same checks enforced by CI:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/djlint src/blog/templates --profile=django --check
.venv/bin/djlint src/blog/templates --profile=django --lint
.venv/bin/python src/manage.py check
.venv/bin/python src/manage.py makemigrations --check --dry-run
.venv/bin/python src/manage.py test blog mysite --settings=mysite.test_settings
```

Or run the configured local hooks against every tracked file:

```bash
.venv/bin/pre-commit run --all-files
```

## ⇢ Production

The active deployment is a free Render trial using one web service and one
cache, with Neon providing PostgreSQL. It intentionally excludes the Celery
worker and persistent media disk. Start with the
[Deployment runbook](docs/deployment.md), then complete the [Security
checklist](docs/security.md). The full paid profile is preserved under
`unused/render-paid/` for a future production upgrade.

## Documentation

- [Architecture and design decisions](docs/architecture.md)
- [HTTP routes and access rules](docs/routes.md)
- [Render and Neon deployment](docs/deployment.md)
- [Security model and checklist](docs/security.md)
- [Contributing and development workflow](CONTRIBUTING.md)

### Why there is no Swagger page

This project currently exposes server-rendered pages, HTML fragments, RSS, a
sitemap, and operational health responses—not a public JSON REST API. OpenAPI
and Swagger UI would document an API contract that does not exist and add
maintenance overhead. If a versioned API such as `/api/v1/` is introduced, its
schema and interactive documentation should be added with the API itself.
