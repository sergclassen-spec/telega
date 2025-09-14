#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DB="${PROJECT_DIR}/data/posts.db"
BACKUP_DIR="${PROJECT_DIR}/backups"
RCLONE_REMOTE="${RCLONE_REMOTE:-remote:tg_backups}"

mkdir -p "${BACKUP_DIR}"
DATE="$(date +%F_%H%M)"
BACKUP_SQL="${BACKUP_DIR}/posts_${DATE}.db"
BACKUP_TAR="${BACKUP_DIR}/posts_${DATE}.tar.gz"

python3 - <<PY
import sqlite3
conn = sqlite3.connect("${DATA_DB}")
bck = sqlite3.connect("${BACKUP_SQL}")
with bck:
    conn.backup(bck)
bck.close()
conn.close()
PY

tar -czf "${BACKUP_TAR}" -C "${BACKUP_DIR}" "$(basename "${BACKUP_SQL}")"

if command -v rclone >/dev/null 2>&1; then
  rclone copy "${BACKUP_TAR}" "${RCLONE_REMOTE}" || echo "rclone copy failed"
else
  echo "rclone not found; skipping remote copy"
fi

# cleanup older than 30 days
find "${BACKUP_DIR}" -type f -mtime +30 -delete
