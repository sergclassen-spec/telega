# app/utils.py
import os, time, json, logging, glob, random, requests
from PIL import Image
from typing import Optional
from .config import OPENAI_API_KEY, OPENAI_MODEL, EMBEDDING_MODEL, PUBLISHER_BOT_TOKEN, IMAGE_BANK_DIR, GENERATED_IMAGES_DIR, BRAND_TEMPLATE_PATH, LOG_LEVEL

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("app.utils")

os.makedirs(IMAGE_BANK_DIR, exist_ok=True)
os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)


def openai_chat(prompt: str, max_tokens: int = 250, temperature: float = 0.8) -> str:
    """Call OpenAI ChatCompletions via REST (reliable and explicit)."""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set")
        return ""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": OPENAI_MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": temperature}
    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning("OpenAI chat failed (attempt %s): %s", attempt + 1, e)
            time.sleep(2 * (attempt + 1))
    return ""


def openai_embedding(text: str) -> Optional[list]:
    """Get embedding vector from OpenAI REST API; returns list or None."""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set")
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
    """Send text message via Telegram Bot API; raises on HTTP errors."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": channel_id, "text": text, "disable_web_page_preview": True}
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def post_photo_to_channel(token: str, channel_id: str, photo_path: str, caption: str):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(photo_path, "rb") as f:
        files = {"photo": f}
        data = {"chat_id": channel_id, "caption": caption, "disable_web_page_preview": True}
        r = requests.post(url, files=files, data=data, timeout=60)
        r.raise_for_status()
        return r.json()


def get_random_image_from_bank() -> Optional[str]:
    exts = ["jpg", "jpeg", "png", "webp"]
    files = []
    for e in exts:
        files.extend(glob.glob(os.path.join(IMAGE_BANK_DIR, f"**/*.{e}"), recursive=True))
    if not files:
        return None
    return random.choice(files)


def brand_image(src_path: str, out_path: str) -> str:
    try:
        bg = Image.open(src_path).convert("RGBA")
        tpl = Image.open(BRAND_TEMPLATE_PATH).convert("RGBA")
        tpl_w = min(bg.width // 4, tpl.width)
        tpl_h = int(tpl.height * (tpl_w / tpl.width))
        tpl = tpl.resize((tpl_w, tpl_h))
        bg.paste(tpl, (bg.width - tpl.width - 10, bg.height - tpl.height - 10), tpl)
        bg.convert("RGB").save(out_path, "PNG")
        return out_path
    except Exception as e:
        logger.error("brand_image failed: %s", e)
        return src_path
