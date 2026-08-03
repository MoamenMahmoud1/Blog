# Security Model

Security is enforced in layers. No single middleware, permission, or proxy rule
is treated as the complete boundary.

## Trust boundaries

```text
Internet
   │
   ▼
Render TLS edge
   │ trusted forwarded HTTPS metadata
   ▼
Django security middleware
   ├── host validation
   ├── HTTPS redirect + HSTS
   ├── secure session and CSRF cookies
   ├── CSRF validation
   ├── CSP + frame denial + MIME protections
   └── authentication and authorization
        │
        ├── ownership-filtered queries
        ├── model/custom permissions
        └── validated and sanitized content
```

## Implemented controls

### Authentication and authorization

- Django session authentication and password validators are enabled.
- New accounts join a restricted author group automatically.
- Publishing is a separate capability: `blog.publish_post`.
- Dashboard mutation views check both model permission and post ownership.
- Admin paths return `404` unless the user is active and staff or superuser.
- State-changing actions use `POST`; Django CSRF protection remains active.

### Content and uploads

- Markdown is sanitized by `nh3` with explicit tags, attributes, and URL schemes.
- Script and style content is removed from rendered posts.
- Comment bodies are length-limited and validated.
- Profile uploads are limited to 5 MB at form validation.
- Media serving is restricted to existing images under `MEDIA_ROOT/profiles`;
  resolved-path validation prevents directory traversal.
- Browser sniffing is disabled on media and application responses.

### Transport and browser controls

- Production redirects requests to HTTPS.
- Secure cookies, `HttpOnly` sessions, and `SameSite=Lax` are enabled.
- HSTS is enabled for the current hostname.
- CSP restricts scripts, styles, images, frames, forms, and object content.
- Framing is denied and referrers are restricted to the same origin.
- `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are required in production.

### Abuse and operational controls

- Comments are throttled for 30 seconds per post and client address.
- Share emails are throttled for 60 seconds per signed-in user.
- Celery retries transient SMTP failures with backoff and jitter.
- Task time limits prevent indefinitely stuck email work.
- Search input and page numbers are bounded.
- Health responses contain no internal exception details and are not cached.
- Application logs go to standard output for Render collection.

## Secret handling

Never commit:

- Django secret keys or fallback keys
- Neon connection strings
- Redis URLs containing credentials
- SMTP passwords
- private keys, certificates, or production `.env` files

`.gitignore` excludes these common secret locations, but ignore rules are not a
security control. Review staged changes before every push:

```bash
git diff --cached
```

If a secret is exposed, remove it from use immediately and rotate it at the
provider. Deleting it from the latest commit is not sufficient because Git
history, logs, caches, or forks may retain it.

## Production checklist

```text
[ ] DJANGO_DEBUG=False
[ ] DJANGO_SECRET_KEY is unique, random, and at least 50 characters
[ ] DATABASE_URL uses the intended Neon database and TLS
[ ] ALLOWED_HOSTS contains only real public hostnames
[ ] CSRF_TRUSTED_ORIGINS contains only trusted HTTPS origins
[ ] if Celery is enabled, cache and broker use separate Redis services
[ ] if email is enabled, SMTP uses a revocable app password or provider credential
[ ] /health/ready/ returns 200 after deployment
[ ] anonymous and ordinary users receive 404 for /admin/
[ ] Django check --deploy has no unresolved warnings
[ ] GitHub Actions passes before automatic deployment
[ ] dependencies are reviewed through Dependabot pull requests
[ ] backups or Neon restore points exist before destructive migrations
```

Keep `SECURE_HSTS_INCLUDE_SUBDOMAINS=False` and `SECURE_HSTS_PRELOAD=False` until
all subdomains are permanently HTTPS-capable. These settings are intentionally
conservative because enabling them prematurely can make subdomains unreachable.

## Known operational limits

- Rate limits use cache keys and are lightweight abuse controls, not a complete
  anti-spam or distributed denial-of-service service.
- `REMOTE_ADDR` is used for comment throttling; proxy-chain interpretation must
  be reviewed before treating it as a strong client identity.
- Uploaded image content is accepted through Django/Pillow validation, but a
  dedicated object-storage and malware-scanning pipeline would be appropriate
  for higher-risk public uploads.
- Free-trial media is ephemeral. The paid Render disk makes it persistent but
  ties media to one web instance.

## Reporting a vulnerability

Do not publish credentials, exploit details, or personal data in a public issue.
Use the repository owner's private contact channel or GitHub private vulnerability
reporting when it is enabled. Include the affected route, impact, reproduction
steps, and a minimal proof of concept without accessing other users' data.

## Framework references

- [Django security documentation](https://docs.djangoproject.com/en/6.0/topics/security/)
- [Django deployment checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
- [Django content security policy](https://docs.djangoproject.com/en/6.0/ref/csp/)
