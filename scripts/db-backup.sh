#!/bin/bash
# Dumps the database and prunes dumps older than BACKUP_RETENTION_DAYS.
# Executed INSIDE the db container by the server's ofelia daemon
# (see the ofelia.* labels on the db service in docker-compose.yml).
set -euo pipefail

STAMP=$(date +%Y-%m-%d-%H-%M-%S)
TARGET="/var/lib/postgresql/backups/backup_${STAMP}.sql.gz"

pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$TARGET"
echo "$(date -Iseconds) backup written: $TARGET ($(du -h "$TARGET" | cut -f1))"

find /var/lib/postgresql/backups -name 'backup_*.sql.gz' -mtime "+${BACKUP_RETENTION_DAYS:-7}" -delete
