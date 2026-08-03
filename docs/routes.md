# HTTP Route Reference

This is the contract for the application's current HTTP surface. It documents
browser pages, progressive HTML fragments, machine-readable documents, health
checks, and protected management actions.

## Response types

| Kind | Content type | Purpose |
| --- | --- | --- |
| Page | `text/html` | Complete browser document |
| Fragment | `text/html` | Partial markup appended or replaced by JavaScript |
| Feed | RSS/XML | Latest published posts |
| Sitemap | XML | Search-engine discovery |
| Health | `application/json` | Runtime probes |

## Public and account routes

| Method | Path | Access | Response / behavior |
| --- | --- | --- | --- |
| `GET` | `/blog/` | Public | Published-post page; `cursor` loads the next stable batch |
| `GET` | `/blog/tag/<tag_slug>/` | Public | Published posts restricted to one tag |
| `GET` | `/blog/<year>/<month>/<day>/<post>/` | Public | Published post, active comments, and related posts |
| `POST` | `/blog/<post_id>/comment/` | Public | Add a validated comment; throttled per post and client address |
| `GET`, `POST` | `/blog/<post_id>/share/` | Signed-in user | Queue a share email when the Celery deployment profile is active; submissions are throttled per user |
| `GET` | `/blog/search/` | Public | Ranked search; `query` is required and `page` loads another batch |
| `GET` | `/blog/search/suggestions/` | Public | Up to eight suggestion rows as an HTML fragment; uses `q` |
| `GET` | `/blog/feed/` | Public | RSS feed of latest published posts |
| `GET` | `/blog/signup/` | Anonymous | Account creation form |
| `POST` | `/blog/signup/` | Anonymous | Create account, profile, and author-group membership; then sign in |
| `GET`, `POST` | `/blog/login/` | Anonymous | Django session login |
| `POST` | `/blog/logout/` | Signed-in user | End session and return to the post list |
| `GET`, `POST` | `/blog/<pk>/edit/` | Profile owner | Update the owner's profile image |

For progressive requests, `/blog/`, tag lists, and `/blog/search/` return only
the next HTML fragment when the request includes:

```http
X-Requested-With: XMLHttpRequest
```

## Author dashboard

| Method | Path | Required access | Behavior |
| --- | --- | --- | --- |
| `GET` | `/blog/dashboard/` | Signed in | Own posts; superusers can see all posts |
| `GET`, `POST` | `/blog/dashboard/posts/create/` | `blog.add_post` | Preview or create a draft; publishing also needs `blog.publish_post` |
| `GET`, `POST` | `/blog/dashboard/posts/<pk>/edit/` | Owner + `blog.change_post` | Edit allowed post; published edits need publishing capability |
| `GET`, `POST` | `/blog/dashboard/posts/<pk>/delete/` | Owner + `blog.delete_post` | Confirm and delete an owned post |
| `POST` | `/blog/dashboard/posts/<pk>/publish/` | Owner + change + publish permissions | Publish now or keep selected future schedule |
| `POST` | `/blog/dashboard/posts/<pk>/unpublish/` | Owner + change + publish permissions | Return post to draft state |

New non-superuser accounts receive `view_post`, `add_post`, `change_post`, and
`delete_post` through the `Blog authors` group. The custom `publish_post`
permission must be granted separately by an administrator.

The active free Render trial has no Celery broker or worker, so share-email
submission returns the form with a temporary-unavailability message. The paid
profile preserved under `unused/render-paid/` enables delivery.

## Discovery and operations

| Method | Path | Access | Success | Failure |
| --- | --- | --- | --- | --- |
| `GET` | `/sitemap.xml` | Public | XML containing published post URLs | Standard Django error response |
| `GET`, `HEAD` | `/health/live/` | Public | `200 {"status":"ok"}` | Process unreachable |
| `GET`, `HEAD` | `/health/ready/` | Public | `200 {"status":"ok"}` | `503 {"status":"unavailable"}` if database or cache fails |
| `GET` | `/media/profiles/<path>` | Public | Profile image with one-day cache | `404` for missing, non-image, or escaping paths |
| Any admin route | `/admin/...` | Active staff or superuser | Django admin | `404` for anonymous or unauthorized users |

Health responses include `Cache-Control: no-store`. Readiness checks both the
database and cache because the web service depends on both for normal operation.

## Status conventions

- `302` redirects are expected after successful browser form submissions.
- Anonymous users are redirected to login for protected author features.
- Authenticated users without the required permission receive `403`.
- Missing or non-owned post objects resolve as `404` where ownership-filtered
  querysets are used.
- Invalid comment submissions render the post detail page with status `400`.
- Unauthorized admin discovery always returns `404`.

## API documentation policy

There is no public REST or GraphQL API today. Do not describe these HTML routes
as an OpenAPI schema: templates, redirects, CSRF-protected forms, and session
flows are better represented by this route reference and automated endpoint
tests.

If an API is added later:

1. Place it under a versioned prefix such as `/api/v1/`.
2. Define request and response serializers explicitly.
3. Generate and validate an OpenAPI schema in CI.
4. Expose Swagger UI only as a view of that schema, not as the source of truth.
5. Document authentication, rate limits, errors, pagination, and examples.
