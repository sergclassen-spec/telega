# app/utils.py
import glob
import requests
from PIL import Image
import numpy as np
from .config import OPENAI_API_KEY, OPENAI_MODEL, EMBEDDING_MODEL, PUBLISHER_BOT_TOKEN, IMAGE_BANK_DIR, GENERATED_IMAGES_DIR, BRAND_TEMPLATE_PATH

logging.basicConfig(level=os.getenv('LOG_LEVEL','INFO'))
logger = logging.getLogger('app')

os.makedirs(IMAGE_BANK_DIR, exist_ok=True)
os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)

# --- OpenAI ---
def openai_chat(prompt: str, max_tokens: int = 250, temperature: float = 0.8) -> str:
"""Simple OpenAI ChatCompletions caller using REST API.
Returns the generated text or empty string on failure.
"""
if not OPENAI_API_KEY:
logger.error('OpenAI API key not configured')
return ''
headers = {'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'}
payload = {'model': OPENAI_MODEL, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens, 'temperature': temperature}
for attempt in range(3):
try:
r = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload, timeout=30)
r.raise_for_status()
return r.json()['choices'][0]['message']['content'].strip()
except Exception as e:
logger.warning('OpenAI call failed %s (attempt %s)', e, attempt+1)
time.sleep(2*(attempt+1))
return ''

def openai_embedding(text: str):
if not OPENAI_API_KEY:
return None
headers = {'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'}
payload = {'model': EMBEDDING_MODEL, 'input': text}
r = requests.post('https://api.openai.com/v1/embeddings', headers=headers, json=payload, timeout=30)
r.raise_for_status(); return r.json()['data'][0]['embedding']

# --- Telegram posting ---

def post_message_to_channel(token: str, channel_id: str, text: str):
url = f'https://api.telegram.org/bot{token}/sendMessage'
payload = {'chat_id': channel_id, 'text': text, 'disable_web_page_preview': True}
r = requests.post(url, json=payload, timeout=30)
r.raise_for_status()
return r.json()

def post_photo_to_channel(token: str, channel_id: str, photo_path: str, caption: str):
url = f'https://api.telegram.org/bot{token}/sendPhoto'
with open(photo_path, 'rb') as f:
files = {'photo': f}
data = {'chat_id': channel_id, 'caption': caption, 'disable_web_page_preview': True}
r = requests.post(url, data=data, files=files, timeout=60)
r.raise_for_status(); return r.json()

# --- Image Bank ---

def get_random_image_from_bank():
exts = ['jpg', 'jpeg', 'png', 'webp']
files = []
for e in exts:
files.extend(glob.glob(os.path.join(IMAGE_BANK_DIR, f'**/*.{e}'), recursive=True))
if not files:
return None
return random.choice(files)

def brand_image(src_path: str, out_path: str):
try:
bg = Image.open(src_path).convert('RGBA')
tpl = Image.open(BRAND_TEMPLATE_PATH).convert('RGBA')
tpl = tpl.resize((min(bg.width, tpl.width), int(tpl.height * (min(bg.width, tpl.width) / tpl.width))))
bg.paste(tpl, (bg.width - tpl.width - 10, bg.height - tpl.height - 10), tpl)
bg.convert('RGB').save(out_path, 'PNG')
return out_path
except Exception as e:
logger.error('Branding image failed: %s', e)
return src_path
