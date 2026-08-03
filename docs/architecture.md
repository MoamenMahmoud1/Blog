# Architecture

This document describes how the application is divided, how requests move
through it, and why the main implementation choices were made.

## Context

The project is a server-rendered Django monolith. That is intentional: the blog
does not need a separate frontend application or a public REST API. Django owns
routing, validation, authorization, rendering, and persistence, while small
JavaScript modules progressively enhance search and pagination.

```text
┌──────────────────────────────── Application boundary ────────────────────────────────┐
│                                                                                       │
│  URLconf → View → Form ────────────────┐                                               │
│              │                         │                                               │
│              ├→ Selector → Model → PostgreSQL                                         │
│              │                         │                                               │
│              ├→ Service  → Model ──────┘                                               │
│              │                                                                         │
│              ├→ Template → HTML → page-specific CSS/JS                                │
│              │                                                                         │
│              └→ Celery task → Redis broker → Worker → SMTP                            │
│                                                                                       │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

## Layer responsibilities

| Layer | Location | Responsibility |
| --- | --- | --- |
| Routing | `src/*/urls.py` | Stable public paths and route names |
| HTTP adapters | `src/blog/views/` | Parse requests, select templates, and build responses |
| Forms | `src/blog/forms.py` | Validate and normalize user input |
| Permissions | `src/blog/permissions.py` | Capability names and object ownership boundaries |
| Selectors | `src/blog/selectors.py` | Reusable, read-only query construction |
| Services | `src/blog/services.py` | Explicit publication state changes |
| Domain and persistence | `src/blog/models.py` | Stored data, indexes, managers, and invariants |
| Background work | `src/blog/tasks.py` | Retryable email delivery outside web requests |
| Presentation | `templates/`, `static/blog/` | HTML plus feature-scoped styles and behavior |
| Infrastructure | `render.yaml`, `docker/` | Runtime topology and production image |

Views are class-based and grouped by feature rather than kept in one growing
module:

```text
views/
├── public.py      # feed, detail, comments, and sharing
├── search.py      # suggestions and full search
├── accounts.py    # signup, login, logout, and profile
└── dashboard.py   # author post management and publication actions
```

## Read flows

### Public feed

```text
GET /blog/
  → published_posts()
  → indexed order: publish DESC, id DESC
  → fetch page_size + 1 rows
  → sign the last (publish, id) pair
  → render full page or the next HTML fragment
```

The public feed uses keyset pagination. It does not execute a total `COUNT(*)`
and does not slow down by scanning an ever-growing offset. The signed cursor is
opaque to the browser and rejects tampering.

### Search

```text
query
  → SearchForm validation
  → PostgreSQL websearch query
  → weighted title/body search vector
  → GIN-assisted matching
  → rank DESC, publish DESC, id DESC
  → fetch requested slice + 1 row
```

Search uses numbered batches because rank is calculated for each query and the
user may request a specific next batch. It avoids a separate count query and
caps the page number. Suggestions return at most eight results and are marked
`no-store`.

### Post detail

The detail query loads the author, tags, and active comments efficiently.
Related posts are ranked by shared tag count and limited to four rows.

## Write flows

```text
request
  → authentication
  → model permission
  → author-owned queryset
  → form validation
  → publication service
  → database write
```

- New accounts join the `Blog authors` group automatically.
- Authors can create posts and manage their own drafts.
- Publishing or scheduling requires the custom `blog.publish_post` permission.
- Non-superusers never receive another author's posts in management querysets.
- Publication transitions are centralized in `services.py`.

## Frontend strategy

The first request returns complete, usable HTML. JavaScript enhances the page
afterward:

- `search-dialog.js` requests small suggestion fragments.
- `infinite-scroll.js` appends the next post or search-result fragment.
- `theme.js` manages the selected theme.
- CSS and JavaScript are included only by pages that require them, except shared
  shell behavior.

This keeps navigation usable without JavaScript, avoids downloading the full
page for each progressive load, and retains Django's normal template workflow.

## Runtime topology

```text
Render web ──────────────┬──── Neon pooled PostgreSQL
                        ├──── Redis cache
                        └──── persistent profile-media disk

Render worker ──────────┬──── Redis broker
                        ├──── Neon pooled PostgreSQL
                        └──── SMTP provider

Static files: image build → collectstatic → WhiteNoise → immutable hashed assets
```

The application remains synchronous WSGI because its request work is primarily
Django ORM and template rendering. Celery isolates slow email I/O. ASGI entry
points are retained for future use but switching servers alone would not make
the synchronous ORM and views asynchronous.

## Deliberate boundaries

- `unused/vps/` is an archive, not active deployment configuration.
- Uploaded media is not served by WhiteNoise; the application exposes only the
  restricted profile-image subtree from the attached disk.
- Cache and broker use separate Redis services and eviction policies.
- Swagger/OpenAPI is deferred until a real versioned HTTP API exists.

## Further reading

- [Django class-based views](https://docs.djangoproject.com/en/6.0/topics/class-based-views/)
- [Django PostgreSQL full-text search](https://docs.djangoproject.com/en/6.0/ref/contrib/postgres/search/)
- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
