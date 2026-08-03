#!/usr/bin/env bash

set -Eeuo pipefail
umask 077

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
backup_dir="${1:-}"

if [[ -z "$backup_dir" ]]; then
    echo "Usage: RESTORE_CONFIRM=<backup-name> $0 <backup-directory>" >&2
    exit 1
fi

backup_dir="$(realpath -- "$backup_dir")"
backup_name="$(basename -- "$backup_dir")"

if [[ ! -d "$backup_dir" ]]; then
    echo "Backup directory does not exist: $backup_dir" >&2
    exit 1
fi

required_files=(
    "$backup_dir/database.dump"
    "$backup_dir/media.tar.gz"
    "$backup_dir/SHA256SUMS"
)

for required_file in "${required_files[@]}"; do
    if [[ ! -f "$required_file" ]]; then
        echo "Missing backup file: $required_file" >&2
        exit 1
    fi
done

(
    cd -- "$backup_dir"
    sha256sum --check SHA256SUMS
)

if [[ "${RESTORE_CONFIRM:-}" != "$backup_name" ]]; then
    echo "Restore cancelled." >&2
    echo "This operation replaces the current database and media files." >&2
    echo "Run again with:" >&2
    echo "RESTORE_CONFIRM='$backup_name' $0 '$backup_dir'" >&2
    exit 1
fi

cd -- "$project_dir"

docker compose up --detach --wait db
docker compose stop web worker nginx

echo "Restoring database..."

docker compose exec -T db sh -eu -c '
    exec pg_restore \
        --username="$POSTGRES_USER" \
        --dbname="$POSTGRES_DB" \
        --clean \
        --if-exists \
        --no-owner \
        --no-privileges \
        --exit-on-error
' < "$backup_dir/database.dump"

echo "Preparing media volume..."

docker compose run --rm --no-deps volumes-init

echo "Restoring media files..."

docker compose run --rm --no-deps -T web sh -eu -c '
    find /app/media -mindepth 1 -delete
    tar -C /app/media -xzf -
' < "$backup_dir/media.tar.gz"

echo "Applying migrations..."

docker compose run --rm migrate

echo "Collecting static files..."

docker compose run --rm collectstatic

echo "Starting application..."

docker compose up \
    --detach \
    --remove-orphans \
    --wait \
    --wait-timeout 180

echo "Restore completed successfully from: $backup_dir"