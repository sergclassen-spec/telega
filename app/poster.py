# app/poster.py
"""
Publish posts to Telegram channels using publisher bot token.
"""

import logging
import time
from .db import get_conn
from .utils import post_message_to_channel, post_photo_to_channel
from .config import PUBLISHER_BOT_TOKEN, PUBLISHER_CHANNEL_ID, TEST_CHANNEL_ID

logger = logging.getLogger("app.poster")


def publish_post_by_id(post_id: int, to_test: bool = False) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM posts WHERE id=? LIMIT 1", (post_id,)).fetchone()
    if not row:
        conn.close()
        logger.error("Post %s not found", post_id)
        return False

    post = dict(row)
    channel_id = TEST_CHANNEL_ID if to_test and TEST_CHANNEL_ID else (post.get("channel_id") or PUBLISHER_CHANNEL_ID)
    if not channel_id:
        logger.error("No channel specified for post %s and no default publisher channel set", post_id)
        conn.close(); return False

    try:
        if post.get("image_path"):
            post_photo_to_channel(PUBLISHER_BOT_TOKEN, channel_id, post["image_path"], post["text"])
        else:
            post_message_to_channel(PUBLISHER_BOT_TOKEN, channel_id, post["text"])
        now = int(time.time())
        cur.execute("UPDATE posts SET status=?, updated_at=? WHERE id=?", ("published", now, post_id))
        conn.commit()
        logger.info("Published post %s to %s", post_id, channel_id)
        return True
    except Exception as e:
        logger.error("Failed to publish post %s: %s", post_id, e)
        return False
    finally:
        conn.close()


def publish_next_ready(to_test: bool = False) -> int:
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT id FROM posts WHERE status='approved' ORDER BY created_at ASC LIMIT 1").fetchone()
    if not row:
        conn.close(); return 0
    pid = row["id"]
    ok = publish_post_by_id(pid, to_test=to_test)
    conn.close()
    return pid if ok else 0
