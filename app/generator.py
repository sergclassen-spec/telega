# app/generator.py
"""
Generation pipeline:
- Checks moderation queue size (MAX_DRAFTS_IN_QUEUE).
- Generates post text via OpenAI (openai_chat wrapper in utils).
- Stores post with status 'on_moderation'.
- Uses embedding saving for potential future deduplication (optional).
"""

import time, logging, json
from .db import get_conn, ensure_schema, count_posts_with_status
from .utils import openai_chat, openai_embedding
from .config import MAX_DRAFTS_IN_QUEUE, DEFAULT_CATEGORY
import hashlib, os

logger = logging.getLogger("app.generator")

def text_hash(s: str) -> str:
    """Return SHA256 hash for deduplication/uniqueness."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def generate_for_item(item: dict) -> bool:
    """
    Generate a single post and insert as 'on_moderation'.
    Returns True if inserted, False otherwise (e.g., queue full or generation failed).
    """
    ensure_schema()

    # Pause generation if moderation queue is full
    current_on_mod = count_posts_with_status("on_moderation")
    if current_on_mod >= MAX_DRAFTS_IN_QUEUE:
        logger.info("Moderation queue full (%s/%s). Skipping generation.", current_on_mod, MAX_DRAFTS_IN_QUEUE)
        return False

    prompt = (
        f"Generate a provocative Telegram post in Russian (<=280 chars) from this news.\n"
        f"Title: {item.get('title')}\nSummary: {item.get('summary')}\n\n"
        "- Make it intriguing and slightly controversial.\n"
        "- End with an open question to spark comments.\n"
        "- Add 1-2 emojis and 2 relevant hashtags.\n        "
    )

    text = openai_chat(prompt, max_tokens=200, temperature=0.8)
    if not text:
        logger.warning("OpenAI returned empty text for item: %s", item.get("title"))
        return False

    # Optionally compute embedding for later deduplication
    try:
        emb = openai_embedding(text)
        emb_json = json.dumps(emb) if emb is not None else None
    except Exception as e:
        logger.warning("Embedding generation failed: %s", e)
        emb_json = None

    now = int(time.time())
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO posts
               (source_title, source_url, raw_rss, text, image_path, status, channel_id, category, tags, embedding, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                item.get("title"),
                item.get("link"),
                item.get("summary"),
                text,
                None,  # image_path
                "on_moderation",
                item.get("channel_id") or None,
                item.get("category") or DEFAULT_CATEGORY,
                None,
                emb_json,
                now,
                now,
            ),
        )
        conn.commit()
        logger.info("Inserted post into moderation queue (title=%s)", item.get("title"))
        return True
    except Exception as e:
        logger.error("DB insert failed: %s", e)
        return False
    finally:
        conn.close()

def batch_generate(items: list, limit: int = 10) -> int:
    """Batch-generate posts from a list of RSS items (up to limit)."""
    count = 0
    for item in items[:limit]:
        if generate_for_item(item):
            count += 1
        # small delay to avoid rate limits
        time.sleep(1)
    logger.info("Batch generation finished: %s posts created", count)
    return count

if __name__ == "__main__":
    # quick test mode (not used in production)
    sample = [{"title": "Test news", "summary": "Short summary", "link": "http://example"}]
    print(batch_generate(sample, limit=1))
