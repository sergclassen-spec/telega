import os
import time
import logging
import sqlite3
import numpy as np
from openai import OpenAI
from app.db import get_connection, ensure_tables

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========== SETTINGS ==========
MAX_RETRIES = 3
SLEEP_BETWEEN_CALLS = 2
EMBEDDING_MODEL = "text-embedding-3-small"
GENERATION_MODEL = "gpt-4.1-mini"
# ==============================


def generate_embedding(text: str):
    """Generate vector embedding for deduplication."""
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return np.array(resp.data[0].embedding)


def is_duplicate(text: str, conn) -> bool:
    """Check if new text is semantically too close to existing posts."""
    new_emb = generate_embedding(text)
    cur = conn.execute("SELECT embedding FROM posts")
    for row in cur.fetchall():
        old_emb = np.frombuffer(row[0], dtype=np.float32)
        sim = np.dot(new_emb, old_emb) / (np.linalg.norm(new_emb) * np.linalg.norm(old_emb))
        if sim > 0.78:
            logging.info("Duplicate detected, skipping.")
            return True
    return False


def call_openai(prompt: str) -> str:
    """Call OpenAI chat model with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=GENERATION_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.8,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"OpenAI API error (attempt {attempt+1}): {e}")
            time.sleep(SLEEP_BETWEEN_CALLS)
    return ""


def generate_post(item: dict) -> str:
    """
    Generate Telegram post from an RSS news item.
    Workflow:
    1. Use GPT-4.1-mini to write a provocative, intriguing post.
    2. Deduplicate against existing posts.
    3. Save to SQLite if unique.
    """
    conn = get_connection()
    ensure_tables(conn)

    final_prompt = f"""
    Generate a Telegram post (<280 chars) based on this news:
    Title: {item.get("title", "")}
    Summary: {item.get("summary", "")}

    Instructions:
    - Make it provocative and intriguing.
    - End with an open question to spark discussion.
    - Add 2 relevant hashtags.
    - Avoid clichés like 'dreams come true'.
    """

    final_text = call_openai(final_prompt)

    if not final_text or is_duplicate(final_text, conn):
        return ""

    emb = generate_embedding(final_text).astype(np.float32).tobytes()
    conn.execute("INSERT INTO posts (title, text, embedding) VALUES (?, ?, ?)",
                 (item.get("title", ""), final_text, emb))
    conn.commit()
    conn.close()

    return final_text


def generate_from_rss(items: list) -> int:
    """Batch process multiple RSS items into posts."""
    count = 0
    for item in items:
        post = generate_post(item)
        if post:
            logging.info(f"Generated post: {post}")
            count += 1
        time.sleep(1)  # small delay to avoid rate limits
    return count
