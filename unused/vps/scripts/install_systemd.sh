#!/usr/bin/env bash

set -Eeuo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
expected_project_dir="/opt/django-blog"
systemd_source="${project_dir}/deploy/systemd"
systemd_target="/etc/systemd/system"
backup_dir="/var/backups/django-blog"

if ((EUID != 0)); then
    echo "Run this script with sudo." >&2
    exit 1
fi

if [[ "$project_dir" != "$expected_project_dir" ]]; then
    echo "Project must be deployed at: $expected_project_dir" >&2
    exit 1
fi

if ! id deploy >/dev/null 2>&1; then
    echo "The deploy user does not exist." >&2
    exit 1
fi

if ! getent group docker >/dev/null 2>&1; then
    echo "The docker group does not exist." >&2
    exit 1
fi

required_files=(
    "django-blog-backup.service"
    "django-blog-backup.timer"
    "django-blog-tls-renew.service"
    "django-blog-tls-renew.timer"
    "django-blog-backup.service.d/retention.conf"
)

for required_file in "${required_files[@]}"; do
    if [[ ! -f "${systemd_source}/${required_file}" ]]; then
        echo "Missing systemd file: ${required_file}" >&2
        exit 1
    fi
done

install -d -o deploy -g docker -m 0700 "$backup_dir"

install -o root -g root -m 0755 \
    "${project_dir}/scripts/backup.sh" \
    "${project_dir}/scripts/prune_backups.sh" \
    "${project_dir}/scripts/renew_tls.sh" \
    "${project_dir}/scripts/restore.sh" \
    "${project_dir}/scripts/init_tls.sh"

install -o root -g root -m 0644 \
    "${systemd_source}/django-blog-backup.service" \
    "${systemd_target}/django-blog-backup.service"

install -o root -g root -m 0644 \
    "${systemd_source}/django-blog-backup.timer" \
    "${systemd_target}/django-blog-backup.timer"

install -o root -g root -m 0644 \
    "${systemd_source}/django-blog-tls-renew.service" \
    "${systemd_target}/django-blog-tls-renew.service"

install -o root -g root -m 0644 \
    "${systemd_source}/django-blog-tls-renew.timer" \
    "${systemd_target}/django-blog-tls-renew.timer"

install -d -o root -g root -m 0755 \
    "${systemd_target}/django-blog-backup.service.d"

install -o root -g root -m 0644 \
    "${systemd_source}/django-blog-backup.service.d/retention.conf" \
    "${systemd_target}/django-blog-backup.service.d/retention.conf"

systemctl daemon-reload

systemctl enable --now \
    django-blog-backup.timer \
    django-blog-tls-renew.timer

systemctl list-timers \
    django-blog-backup.timer \
    django-blog-tls-renew.timer