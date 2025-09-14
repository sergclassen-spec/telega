# app/poster.py
"""
Poster module: publish posts from DB to Telegram channels.
Supports publisher token (PUBLISHER_BOT_TOKEN) and optional test channel.
"""

import time, logging
from .db import get_conn
from .utils import post_message_to_channel, post_photo_to_channel
from .config import PUBLISHER_BOT_TOKEN, PUBLISHER_CHANNEL_ID, TEST_CHANNEL_ID

logger = logging.getLogger("app.poster")


def publish_post_by_id(post_id: int, to_test: bool = False) -> bool:
    """
    Publish a post with given id.
    If to_test=True, publish to TEST_CHANNEL_ID, else to post['channel_id'] or default PUBLISHER_CHANNEL_ID.
    Returns True on success, False otherwise.
    """
    conn = get_conn(); cur = conn.cursor()
    row = cur.execute("SELECT * FROM posts WHERE id=? LIMIT 1", (post_id,)).fetchone()
    if not row:
        conn.close(); logger.error("Post %s not found", post_id); return False

    post = dict(row)
    channel_id = TEST_CHANNEL_ID if to_test else (post.get("channel_id") or PUBLISHER_CHANNEL_ID)

    try:
        if post.get("image_path"):
            # publish photo with caption
            post_photo_to_channel(PUBLISHER_BOT_TOKEN, channel_id, post["image_path"], post["text"])
        else:
            post_message_to_channel(PUBLISHER_BOT_TOKEN, channel_id, post["text"])
        # update status
        now = int(time.time())
        cur.execute("UPDATE posts SET status=?, updated_at=? WHERE id=?", ("published", now, post_id))
        conn.commit()
        logger.info("Published post %s to channel %s", post_id, channel_id)
        return True
    except Exception as e:
        logger.error("Failed to publish post %s: %s", post_id, e)
        return False
    finally:
        conn.close()


def publish_next_ready(to_test: bool = False) -> int:
    """
    Publish the next post that has status 'approved' (for workflows using approval).
    Returns published post id or 0 if none.
    """
    conn = get_conn(); cur = conn.cursor()
    row = cur.execute("SELECT id FROM posts WHERE status='approved' ORDER BY created_at ASC LIMIT 1").fetchone()
    if not row:
        conn.close(); return 0
    pid = row["id"]
    ok = publish_post_by_id(pid, to_test=to_test)
    conn.close()
    return pid if ok else 0
