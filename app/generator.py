# app/generator.py
"""
Generation pipeline:
- Checks moderation queue size (MAX_DRAFTS_IN_QUEUE).
- Generates post text via OpenAI (openai_chat wrapper in utils).
- Stores post with status 'on_moderation'.
"""

import time
import logging
import json
from .db import get_conn, ensure_schema, count_posts_with_status
from .utils import openai_chat, openai_embedding
from .config import MAX_DRAFTS_IN_QUEUE, DEFAULT_CATEGORY
import hashlib

logger = logging.getLogger("app.generator")

def text_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def generate_for_item(item: dict) -> bool:
    ensure_schema()
    current_on_mod = count_posts_with_status("on_moderation")
    if current_on_mod >= MAX_DRAFTS_IN_QUEUE:
        logger.info("Moderation queue full (%s/%s). Skipping generation.", current_on_mod, MAX_DRAFTS_IN_QUEUE)
        return False

    prompt = (
        f"Generate a provocative Telegram post in Russian (<=280 chars) from this news.\n"
        f"Title: {item.get('title')}\nSummary: {item.get('summary')}\n\n"
        "- Make it intriguing and slightly controversial.\n"
        "- End with an open question to spark comments.\n"
        "- Add 1-2 emojis and 2 relevant hashtags.\n"
    )

    text = openai_chat(prompt, max_tokens=200, temperature=0.8)
    if not text:
        logger.warning("OpenAI returned empty text")
        return False

    emb = None
    try:
        emb = openai_embedding(text)
    except Exception as e:
        logger.warning("embedding error: %s", e)

    now = int(time.time())
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            """INSERT INTO posts
               (source_title, source_url, raw_rss, text, image_path, status, channel_id, category, tags, embedding, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                item.get("title"),
                item.get("link"),
                item.get("summary"),
                text,
                None,
                "on_moderation",
                item.get("channel_id") or None,
                item.get("category") or DEFAULT_CATEGORY,
                None,
                json.dumps(emb) if emb is not None else None,
                now,
                now,
            ),
        )
        conn.commit()
        logger.info("Inserted new post into moderation queue")
        return True
    except Exception as e:
        logger.error("DB insert failed: %s", e)
        return False
    finally:
        conn.close()

def batch_generate(items: list, limit: int = 10) -> int:
    count = 0
    for item in items[:limit]:
        if generate_for_item(item):
            count += 1
        time.sleep(1)
    logger.info("Batch generate completed: %s", count)
    return count
