# app/poster.py
import time, logging
from .db import get_conn
from .utils import post_message_to_channel, post_photo_to_channel
from .config import PUBLISHER_BOT_TOKEN, PUBLISHER_CHANNEL_ID, TEST_CHANNEL_ID

logger = logging.getLogger("app.poster")


def publish_post_by_id(post_id: int, to_test: bool = False) -> bool:
    conn = get_conn(); cur = conn.cursor()
    row = cur.execute("SELECT * FROM posts WHERE id=? LIMIT 1", (post_id,)).fetchone()
    if not row:
        conn.close(); logger.error("Post %s not found", post_id); return False
    post = dict(row)
    channel = TEST_CHANNEL_ID if to_test and TEST_CHANNEL_ID else (post.get("channel_id") or PUBLISHER_CHANNEL_ID)
    if not channel:
        conn.close(); logger.error("No channel configured to publish"); return False
    try:
        if post.get("image_path"):
            post_photo_to_channel(PUBLISHER_BOT_TOKEN, channel, post["image_path"], post["text"])
        else:
            post_message_to_channel(PUBLISHER_BOT_TOKEN, channel, post["text"])
        now = int(time.time())
        cur.execute("UPDATE posts SET status=?, updated_at=? WHERE id=?", ("published", now, post_id))
        conn.commit()
        logger.info("Published post %s to %s", post_id, channel)
        return True
    except Exception as e:
        logger.error("Failed to publish: %s", e)
        return False
    finally:
        conn.close()


def publish_next_ready(to_test: bool = False) -> int:
    conn = get_conn(); cur = conn.cursor()
    row = cur.execute("SELECT id FROM posts WHERE status='approved' ORDER BY created_at ASC LIMIT 1").fetchone()
    conn.close()
    if not row:
        return 0
    pid = row["id"]
    ok = publish_post_by_id(pid, to_test=to_test)
    return pid if ok else 0
