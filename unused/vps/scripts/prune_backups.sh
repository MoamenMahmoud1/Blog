#!/usr/bin/env bash

set -Eeuo pipefail

backup_root="${BACKUP_DIR:?BACKUP_DIR must be set}"
retention_days="${BACKUP_RETENTION_DAYS:-30}"

if [[ ! "$retention_days" =~ ^[0-9]+$ ]] || ((retention_days < 1)); then
    echo "BACKUP_RETENTION_DAYS must be a positive integer." >&2
    exit 1
fi

if [[ ! -d "$backup_root" ]]; then
    echo "Backup directory does not exist: $backup_root" >&2
    exit 1
fi

backup_root="$(realpath -- "$backup_root")"

if [[ "$backup_root" == "/" ]]; then
    echo "BACKUP_DIR cannot be /" >&2
    exit 1
fi

find "$backup_root" \
    -mindepth 1 \
    -maxdepth 1 \
    -type d \
    -name 'blog-????-??-??T??-??-??Z' \
    -mtime "+$retention_days" \
    -print \
    -exec rm -rf -- {} +