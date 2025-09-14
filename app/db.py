# app/db.py
"""
DB helpers: connection factory, schema ensure, counts and cleanup queries.
"""

import sqlite3
import os
import time
from typing import List, Tuple
from .config import DB_PATH

# ensure directory
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_conn():
    """Return a sqlite3 connection with WAL enabled and row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def ensure_schema():
    """Create tables and indexes if missing."""
    conn = get_conn()
    c = conn.cursor()
    c.executescript(
        """
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_title TEXT,
        source_url TEXT,
        raw_rss TEXT,
        text TEXT,
        image_path TEXT,
        status TEXT,
        channel_id INTEGER,
        category TEXT,
        tags TEXT,
        embedding TEXT,
        created_at INTEGER,
        updated_at INTEGER
    );

    CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
    CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at);

    CREATE TABLE IF NOT EXISTS affiliates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_url TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS clicks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        affiliate_id INTEGER,
        post_id INTEGER,
        ts INTEGER,
        ip TEXT,
        ua TEXT
    );
    """
    )
    conn.commit()
    conn.close()


def count_posts_with_status(status: str) -> int:
    conn = get_conn()
    c = conn.cursor()
    r = c.execute("SELECT COUNT(1) as cnt FROM posts WHERE status = ?", (status,)).fetchone()
    conn.close()
    return int(r["cnt"]) if r else 0


def get_old_rejected_and_stale(on_moderation_days: int, rejected_hours: int) -> List[Tuple[int, str]]:
    """Return list of (id, image_path) of posts to delete by time thresholds."""
    now = int(time.time())
    stale_ts = now - int(on_moderation_days) * 86400
    rejected_ts = now - int(rejected_hours) * 3600
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute(
        """
        SELECT id, image_path FROM posts
        WHERE (status='rejected' AND updated_at<?)
           OR (status='on_moderation' AND updated_at<?)
    """,
        (rejected_ts, stale_ts),
    ).fetchall()
    conn.close()
    return [(r["id"], r["image_path"]) for r in rows]
