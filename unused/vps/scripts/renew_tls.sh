#!/usr/bin/env bash

set -Eeuo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

cd -- "$project_dir"

if [[ -z "$(docker compose ps --status running --quiet nginx)" ]]; then
    echo "Nginx must be running before certificate renewal." >&2
    exit 1
fi

docker compose \
    --profile tools \
    run \
    --rm \
    certbot \
    renew \
    --webroot \
    --webroot-path=/var/www/certbot \
    --non-interactive \
    --quiet

docker compose exec -T nginx nginx -t
docker compose exec -T nginx nginx -s reload

echo "TLS certificate renewal check completed successfully."