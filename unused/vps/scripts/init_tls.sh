#!/usr/bin/env bash

set -Eeuo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${project_dir}/.env"

if [[ ! -f "$env_file" ]]; then
    echo "Missing environment file: $env_file" >&2
    exit 1
fi

read_env_value() {
    local key="$1"

    sed -n "s/^${key}=//p" "$env_file" |
        tail -n 1 |
        tr -d '\r'
}

site_domain="$(read_env_value SITE_DOMAIN)"
acme_email="$(read_env_value ACME_EMAIL)"

if [[ ! "$site_domain" =~ ^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$ ]]; then
    echo "SITE_DOMAIN is missing or invalid." >&2
    exit 1
fi

if [[ ! "$acme_email" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]]; then
    echo "ACME_EMAIL is missing or invalid." >&2
    exit 1
fi

cd -- "$project_dir"

nginx_was_running=false

if [[ -n "$(docker compose ps --status running --quiet nginx)" ]]; then
    nginx_was_running=true
    docker compose stop nginx
fi

restore_nginx_on_error() {
    if [[ "$nginx_was_running" == true ]]; then
        docker compose up --detach nginx || true
    fi
}

trap restore_nginx_on_error ERR INT TERM

certbot_arguments=(
    certonly
    --standalone
    --non-interactive
    --agree-tos
    --no-eff-email
    --email "$acme_email"
    --domain "$site_domain"
)

if [[ "${LETSENCRYPT_STAGING:-false}" == "true" ]]; then
    certbot_arguments+=(--staging)
fi

docker compose \
    --profile tools \
    run \
    --rm \
    --service-ports \
    certbot \
    "${certbot_arguments[@]}"

trap - ERR INT TERM

docker compose up --detach nginx
docker compose exec -T nginx nginx -t

echo "HTTPS certificate created successfully for: $site_domain"