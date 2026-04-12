#!/bin/bash

# ============================================================================
# Database Backup Script
# ============================================================================
# Creates timestamped backups for the active local database setup.
# - Preferred path: Docker Compose Postgres service (`pg_dump -Fc`)
# - Fallback path: legacy SQLite file copy for non-containerized setups
# Usage: ./backup-database.sh
# ============================================================================

set -euo pipefail

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
POSTGRES_BACKUP_FILE="${BACKUP_DIR}/socratic_tutor-${TIMESTAMP}.dump"
SQLITE_DB_FILE="./data/socratic_tutor.db"
SQLITE_BACKUP_FILE="${BACKUP_DIR}/socratic_tutor-${TIMESTAMP}.db"

POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-socratic_tutor}"
POSTGRES_USER="${POSTGRES_USER:-app_user}"

mkdir -p "${BACKUP_DIR}"

backup_postgres() {
    echo "📦 Creating PostgreSQL backup from Docker Compose service '${POSTGRES_SERVICE}'..."
    docker compose exec -T "${POSTGRES_SERVICE}" \
        pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -Fc > "${POSTGRES_BACKUP_FILE}"

    if [ ! -s "${POSTGRES_BACKUP_FILE}" ]; then
        echo "❌ Error: PostgreSQL backup file is empty"
        exit 1
    fi

    BACKUP_SIZE=$(du -h "${POSTGRES_BACKUP_FILE}" | cut -f1)
    echo "✅ PostgreSQL backup created successfully!"
    echo "   Location: ${POSTGRES_BACKUP_FILE}"
    echo "   Size: ${BACKUP_SIZE}"
    echo "   Restore command:"
    echo "     docker compose exec -T ${POSTGRES_SERVICE} pg_restore -U ${POSTGRES_USER} -d ${POSTGRES_DB} --clean --if-exists < ${POSTGRES_BACKUP_FILE}"
}

backup_sqlite() {
    echo "📦 Creating legacy SQLite backup..."
    cp "${SQLITE_DB_FILE}" "${SQLITE_BACKUP_FILE}"

    if [ ! -f "${SQLITE_BACKUP_FILE}" ]; then
        echo "❌ Error: SQLite backup failed"
        exit 1
    fi

    BACKUP_SIZE=$(du -h "${SQLITE_BACKUP_FILE}" | cut -f1)
    echo "✅ SQLite backup created successfully!"
    echo "   Location: ${SQLITE_BACKUP_FILE}"
    echo "   Size: ${BACKUP_SIZE}"
}

if docker compose ps --services --filter status=running | grep -qx "${POSTGRES_SERVICE}"; then
    backup_postgres
elif [ -f "${SQLITE_DB_FILE}" ]; then
    backup_sqlite
else
    echo "❌ Error: No running Docker Compose Postgres service found and no SQLite database at ${SQLITE_DB_FILE}"
    exit 1
fi

echo ""
echo "🧹 Cleaning up old backups (keeping last 10)..."
ls -t "${BACKUP_DIR}"/socratic_tutor-* 2>/dev/null | tail -n +11 | xargs -r rm
BACKUP_COUNT=$(find "${BACKUP_DIR}" -maxdepth 1 -type f -name 'socratic_tutor-*' | wc -l | tr -d ' ')
echo "   Current backups: ${BACKUP_COUNT}"

echo ""
echo "✅ Backup complete!"
