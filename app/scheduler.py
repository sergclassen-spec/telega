# app/scheduler.py
import time, logging
from apscheduler.schedulers.background import BackgroundScheduler
from .rss_fetcher import fetch_rss
from .generator import batch_generate
from .db import get_old_rejected_and_stale, ensure_schema, get_conn
from .config import DRAFT_POSTS_LIFETIME_DAYS, REJECTED_POSTS_LIFETIME_HOURS, AUTO_DELETE_ENABLED, SCHEDULER_INTERVAL_MIN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.scheduler")


def job_fetch_and_generate():
    try:
        items = fetch_rss()
        batch_generate(items, limit=10)
    except Exception as e:
        logger.exception("Fetch/generate job failed: %s", e)


def cleanup_job():
    if not AUTO_DELETE_ENABLED:
        logger.info("Auto-delete disabled")
        return
    logger.info("Cleanup job started")
    pairs = get_old_rejected_and_stale(DRAFT_POSTS_LIFETIME_DAYS, REJECTED_POSTS_LIFETIME_HOURS)
    conn = get_conn(); cur = conn.cursor()
    for pid, img in pairs:
        try:
            if img and os.path.exists(img):
                os.remove(img)
            cur.execute("DELETE FROM posts WHERE id=?", (pid,))
            logger.info("Deleted post %s", pid)
        except Exception as e:
            logger.exception("Failed to delete post %s: %s", pid, e)
    conn.commit(); conn.close()


def start():
    ensure_schema()
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_fetch_and_generate, "interval", minutes=SCHEDULER_INTERVAL_MIN, id="gen")
    scheduler.add_job(cleanup_job, "interval", hours=6, id="cleanup")
    scheduler.start()
    logger.info("Scheduler started")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()


if __name__ == "__main__":
    start()
