# app/generator.py
# Generation pipeline: respects MAX_DRAFTS_IN_QUEUE and writes new posts into 'on_moderation' status.
import time, logging
from .db import get_conn, ensure_schema, count_posts_with_status
from .utils import openai_chat, openai_embedding
from .config import MAX_DRAFTS_IN_QUEUE, DEFAULT_CATEGORY
import hashlib, json

logger = logging.getLogger('app.generator')

def text_hash(s: str) -> str:
return hashlib.sha256(s.encode('utf-8')).hexdigest()

def generate_for_item(item: dict) -> bool:
"""Generate a single post from an RSS item and insert to DB as 'on_moderation'.
Returns True if inserted, False otherwise.
"""
ensure_schema()
# Pause generation if moderation queue is full
current_on_mod = count_posts_with_status('on_moderation')
if current_on_mod >= MAX_DRAFTS_IN_QUEUE:
logger.info('Moderation queue full (%s/%s). Skipping generation.', current_on_mod, MAX_DRAFTS_IN_QUEUE)
return False

prompt = f"Generate a provocative Telegram post (<280 chars) from this news. Title: {item.get('title')} Summary: {item.get('summary')}"
text = openai_chat(prompt)
if not text:
logger.warning('OpenAI returned empty text')
return False

emb = openai_embedding(text)
now = int(time.time())
conn = get_conn(); c = conn.cursor()
h = text_
