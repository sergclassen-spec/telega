# app/utils.py
"""
Common utilities:
- OpenAI wrappers (chat + embeddings using REST)
- Telegram posting helpers (sendMessage, sendPhoto)
- Image bank helpers (random image, brand overlay)
"""

import os
import time
import json
import logging
import glob
import random
import requests
from PIL import Image
from typing import Optional
from .config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    EMBEDDING_MODEL,
    PUBLISHER_BOT_TOKEN,
    IMAGE_BANK_DIR,
    GENERATED_IMAGES_DIR,
    BRAND_TEMPLATE_PATH,
)

logger = logging.getLogger("app.utils")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

os.makedirs(IMAGE_BANK_DIR, exist_ok=True)
os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)


def openai_chat(prompt: str, max_tokens: int = 250, temperature: float = 0.8) -> str:
    """Call OpenAI chat completions (REST). Returns text or empty string."""
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not set")
        return ""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": OPENAI_MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": temperature}
    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning("OpenAI chat failed (attempt %s): %s", attempt + 1, e)
            time.sleep(2 * (attempt + 1))
    return ""


def openai_embedding(text: str) -> Optional[list]:
    """Get embedding vector from OpenAI REST API. Returns list or None."""
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not set for embeddings")
        return None
    url = "https://api.openai.com/v1/embeddings"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": EMBEDDING_MODEL, "input": text}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]
    except Exception as e:
        logger.warning("OpenAI embedding failed: %s", e)
        return None


def post_message_to_channel(token: str, channel_id: str, text: str):
    """Send text message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": channel_id, "text": text, "disable_web_page_preview": True}
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def post_photo_to_channel(token: str, channel_id: str, photo_path: str, caption: str):
    """Send photo with caption to Telegram channel."""
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(photo_path, "rb") as f:
        files = {"photo": f}
        data = {"chat_id": channel_id, "caption": caption, "disable_web_page_preview": True}
        r = requests.post(url, data=data, files=files, timeout=60)
        r.raise_for_status()
        return r.json()


def get_random_image_from_bank() -> Optional[str]:
    """Return a random image path from IMAGE_BANK_DIR, or None."""
    exts = ["jpg", "jpeg", "png", "webp"]
    files = []
    for e in exts:
        files.extend(glob.glob(os.path.join(IMAGE_BANK_DIR, f"**/*.{e}"), recursive=True))
    if not files:
        return None
    return random.choice(files)


def brand_image(src_path: str, out_path: str) -> str:
    """Overlay brand template onto source image and save to out_path. Return out_path or src_path on failure."""
    try:
        bg = Image.open(src_path).convert("RGBA")
        tpl = Image.open(BRAND_TEMPLATE_PATH).convert("RGBA")
        # Resize template to fit proportionally
        tpl_w = min(bg.width // 4, tpl.width)
        tpl_h = int(tpl.height * (tpl_w / tpl.width))
        tpl = tpl.resize((tpl_w, tpl_h))
        bg.paste(tpl, (bg.width - tpl.width - 10, bg.height - tpl.height - 10), tpl)
        bg.convert("RGB").save(out_path, "PNG")
        return out_path
    except Exception as e:
        logger.error("brand_image failed: %s", e)
        return src_path
