#!/usr/bin/env bash

set -Eeuo pipefail
umask 077

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
backup_root="${BACKUP_DIR:?BACKUP_DIR must be set}"
timestamp="$(date -u +'%Y-%m-%dT%H-%M-%SZ')"
backup_name="blog-${timestamp}"
temporary_dir=""

if [[ "$backup_root" == "/" ]]; then
    echo "BACKUP_DIR cannot be /" >&2
    exit 1
fi

mkdir -p -- "$backup_root"
backup_root="$(realpath -- "$backup_root")"
temporary_dir="$(mktemp -d --tmpdir="$backup_root" ".${backup_name}.XXXXXX")"
final_dir="${backup_root}/${backup_name}"

cleanup() {
    if [[ -n "$temporary_dir" && -d "$temporary_dir" ]]; then
        rm -rf -- "$temporary_dir"
    fi
}

trap cleanup EXIT INT TERM

cd -- "$project_dir"

docker compose exec -T db sh -eu -c '
    exec pg_dump \
        --username="$POSTGRES_USER" \
        --dbname="$POSTGRES_DB" \
        --format=custom \
        --compress=gzip:9 \
        --no-owner \
        --no-privileges
' > "${temporary_dir}/database.dump"

docker compose exec -T nginx \
    tar -C /srv/media -czf - . \
    > "${temporary_dir}/media.tar.gz"

test -s "${temporary_dir}/database.dump"
test -s "${temporary_dir}/media.tar.gz"

(
    cd -- "$temporary_dir"
    sha256sum database.dump media.tar.gz > SHA256SUMS
)

mv -- "$temporary_dir" "$final_dir"
temporary_dir=""

echo "Backup created: ${final_dir}"