# app/generator.py
import time, logging, json
from .db import get_conn, ensure_schema, count_posts_with_status
from .utils import openai_chat, openai_embedding
from .config import MAX_DRAFTS_IN_QUEUE, DEFAULT_CATEGORY
import os

logger = logging.getLogger("app.generator")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


def _is_similar(new_emb, stored_emb_json, threshold=0.78):
    """Compare embedding lists (new_emb is list/iterable)."""
    try:
        import numpy as np
        stored = json.loads(stored_emb_json)
        a = np.array(new_emb); b = np.array(stored)
        if a.size == 0 or b.size == 0:
            return False
        sim = float((a @ b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        return sim >= threshold
    except Exception:
        return False


def generate_for_item(item: dict) -> bool:
    ensure_schema()
    current = count_posts_with_status("on_moderation")
    if current >= MAX_DRAFTS_IN_QUEUE:
        logger.info("Moderation queue full (%s/%s). Skipping generation.", current, MAX_DRAFTS_IN_QUEUE)
        return False

    prompt = (
        f"Generate a provocative Telegram post in Russian (<=280 chars) from this news.\n"
        f"Title: {item.get('title')}\nSummary: {item.get('summary')}\n\n"
        "- Make it intriguing and slightly controversial.\n- End with an open question.\n- Add 1-2 emojis and 2 relevant hashtags."
    )
    text = openai_chat(prompt, max_tokens=200, temperature=0.8)
    if not text:
        logger.warning("OpenAI returned empty text for %s", item.get("title"))
        return False

    emb = openai_embedding(text)
    conn = get_conn(); cur = conn.cursor()

    # basic deduplication using embeddings (if exist)
    if emb:
        rows = cur.execute("SELECT id, embedding FROM posts WHERE embedding IS NOT NULL").fetchall()
        for r in rows:
            if r["embedding"] and _is_similar(emb, r["embedding"]):
                logger.info("Detected semantic duplicate against post %s; skipping", r["id"])
                conn.close()
                return False

    now = int(time.time())
    try:
        cur.execute("""INSERT INTO posts
            (source_title, source_url, raw_rss, text, image_path, status, channel_id, category, tags, embedding, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (item.get("title"), item.get("link"), item.get("summary"), text, None, "on_moderation",
                     item.get("channel_id"), item.get("category") or DEFAULT_CATEGORY, None,
                     json.dumps(emb) if emb is not None else None, now, now))
        conn.commit()
        logger.info("Inserted post into moderation queue")
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
    logger.info("Batch generation done: %s", count)
    return count
