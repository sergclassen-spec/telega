# app/scheduler.py
"""
Scheduler orchestrates:
- periodic RSS fetch + batch generation (generator.batch_generate)
- periodic cleanup for stale/rejected posts
- optional periodic notification jobs (if desired)
"""

import time, logging
from apscheduler.schedulers.background import BackgroundScheduler
from .rss_fetcher import fetch_rss
from .generator import batch_generate
from .db import get_old_rejected_and_stale, get_conn, ensure_schema
from .config import DRAFT_POSTS_LIFETIME_DAYS, REJECTED_POSTS_LIFETIME_HOURS, AUTO_DELETE_ENABLED
import os

logger = logging.getLogger("app.scheduler")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

scheduler = BackgroundScheduler()


def job_fetch_and_generate():
    logger.info("Job: fetch RSS and generate")
    items = fetch_rss()
    generated = batch_generate(items, limit=10)
    logger.info("Generated %s posts", generated)


def cleanup_job():
    if not AUTO_DELETE_ENABLED:
        logger.info("Auto-delete disabled; skipping cleanup.")
        return
    logger.info("Running cleanup job")
    pairs = get_old_rejected_and_stale(DRAFT_POSTS_LIFETIME_DAYS, REJECTED_POSTS_LIFETIME_HOURS)
    conn = get_conn(); cur = conn.cursor()
    for pid, img in pairs:
        try:
            if img and os.path.exists(img):
                os.remove(img)
            cur.execute("DELETE FROM posts WHERE id=?", (pid,))
            logger.info("Deleted post %s and image %s", pid, img)
        except Exception as e:
            logger.error("Failed to delete post %s: %s", pid, e)
    conn.commit(); conn.close()


def start():
    ensure_schema()
    # Fetch+generate every hour
    scheduler.add_job(job_fetch_and_generate, "interval", hours=1, id="gen_job")
    # Cleanup job every 6 hours
    scheduler.add_job(cleanup_job, "interval", hours=6, id="cleanup_job")
    scheduler.start()
    logger.info("Scheduler started.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
