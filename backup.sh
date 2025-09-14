#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB="${PROJECT_DIR}/data/posts.db"
BACKUP_DIR="${PROJECT_DIR}/backups"
RCLONE_REMOTE="${RCLONE_REMOTE:-remote:tg_backups}"

mkdir -p "${BACKUP_DIR}"
DATE="$(date +%F_%H%M)"
OUT_DB="${BACKUP_DIR}/posts_${DATE}.db"
OUT_TAR="${BACKUP_DIR}/posts_${DATE}.tar.gz"

python3 - <<PY
import sqlite3
conn = sqlite3.connect("${DB}")
bck = sqlite3.connect("${OUT_DB}")
with bck:
    conn.backup(bck)
bck.close()
conn.close()
PY

tar -czf "${OUT_TAR}" -C "${BACKUP_DIR}" "$(basename "${OUT_DB}")"

if command -v rclone >/dev/null 2>&1; then
  rclone copy "${OUT_TAR}" "${RCLONE_REMOTE}" || echo "rclone copy failed"
else
  echo "rclone not found; skipping upload"
fi

find "${BACKUP_DIR}" -type f -mtime +30 -delete
