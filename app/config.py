# app/config.py
"""
Centralized configuration. Fill values in environment or .env file.
"""
import os
from typing import Dict

# APIs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Telegram
MODERATOR_BOT_TOKEN = os.getenv("MODERATOR_BOT_TOKEN", "")
PUBLISHER_BOT_TOKEN = os.getenv("PUBLISHER_BOT_TOKEN", "")
MODERATOR_CHAT_ID = int(os.getenv("MODERATOR_CHAT_ID", "0"))  # moderator user id
PUBLISHER_CHANNEL_ID = os.getenv("PUBLISHER_CHANNEL_ID", "")  # default publisher channel id
TEST_CHANNEL_ID = os.getenv("TEST_CHANNEL_ID", "")  # optional test channel id

# Channel mapping (use ints for channel ids)
CHANNELS: Dict[int, str] = {}  # example: {-1001234567890: "Finance"}

# Moderation & Generation Limits
MAX_DRAFTS_IN_QUEUE = int(os.getenv("MAX_DRAFTS_IN_QUEUE", "10"))
REJECTED_POSTS_LIFETIME_HOURS = int(os.getenv("REJECTED_POSTS_LIFETIME_HOURS", "24"))
DRAFT_POSTS_LIFETIME_DAYS = int(os.getenv("DRAFT_POSTS_LIFETIME_DAYS", "2"))
AUTO_DELETE_ENABLED = os.getenv("AUTO_DELETE_ENABLED", "1") == "1"

# Paths
DB_PATH = os.getenv("DB_PATH", "./data/posts.db")
IMAGE_BANK_DIR = os.getenv("IMAGE_BANK_DIR", "./data/image_bank/")
GENERATED_IMAGES_DIR = os.getenv("GENERATED_IMAGES_DIR", "./data/images/")
BRAND_TEMPLATE_PATH = os.getenv("BRAND_TEMPLATE_PATH", "./app/assets/brand_template.png")

# Categories & defaults
AVAILABLE_CATEGORIES = os.getenv("AVAILABLE_CATEGORIES", "finance,technology,health").split(",")
DEFAULT_CATEGORY = os.getenv("DEFAULT_CATEGORY", AVAILABLE_CATEGORIES[0] if AVAILABLE_CATEGORIES else "general")

# Other
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
RCLONE_REMOTE = os.getenv("RCLONE_REMOTE", "remote:tg_backups")
TRACKER_PORT = int(os.getenv("TRACKER_PORT", "5000"))
