# Contributing

Thank you for improving Django Blog. Keep changes focused, testable, and easy to
review.

## Development workflow

1. Create a branch from `main`.
2. Copy `example.env` to `.env` and configure local services.
3. Install both runtime and development dependencies.
4. Make one cohesive change with tests and documentation where needed.
5. Run the local quality checks.
6. Open a pull request after CI passes.

```bash
python -m venv .venv
.venv/bin/python -m pip install --requirement requirements-dev.txt
cp example.env .env
.venv/bin/pre-commit install
```

## Code boundaries

Use the existing structure instead of growing a single module:

- Put request and response orchestration in the matching `views/` feature file.
- Put reusable read-only ORM construction in `selectors.py`.
- Put state-changing domain operations in `services.py`.
- Put access rules and permission constants in `permissions.py`.
- Put retryable external work in `tasks.py`.
- Keep shared layout assets in the base template and feature assets on the pages
  that need them.

Prefer Django's built-in behavior where it clearly solves the requirement.
Introduce a dependency only when it reduces total complexity and has an explicit
owner, configuration, tests, and update path.

## Database changes

Create migrations for model changes:

```bash
.venv/bin/python src/manage.py makemigrations
.venv/bin/python src/manage.py migrate
```

Before submitting, confirm no model change is missing a migration:

```bash
.venv/bin/python src/manage.py makemigrations --check --dry-run
```

Production migrations should be safe during rolling deployment. Separate
destructive cleanup from the release that stops using the old schema.

## Tests and quality gates

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/djlint src/blog/templates --profile=django --check
.venv/bin/djlint src/blog/templates --profile=django --lint
.venv/bin/python src/manage.py check
.venv/bin/python src/manage.py makemigrations --check --dry-run
.venv/bin/python src/manage.py test blog mysite --settings=mysite.test_settings
```

Tests should cover the observable contract: status code, redirects, rendered
content, permissions, ownership, database effects, query behavior when relevant,
and failure paths. Endpoint changes must also update `docs/routes.md`.

## Pull requests

A useful pull request explains:

- what user or operational problem it solves;
- the chosen design and important trade-offs;
- database, environment, deployment, or security impact;
- how it was verified;
- screenshots for visible UI changes.

Never include `.env`, credentials, database dumps, user uploads, or generated
`staticfiles/` in a commit.
