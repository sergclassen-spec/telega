# app/config.py
import os
from typing import Dict

# Load from environment (.env recommended)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Telegram
PUBLISHER_BOT_TOKEN = os.getenv("PUBLISHER_BOT_TOKEN", "")  # used to publish posts
PUBLISHER_CHANNEL_ID = os.getenv("PUBLISHER_CHANNEL_ID", "")  # e.g. -100...
TEST_CHANNEL_ID = os.getenv("TEST_CHANNEL_ID", "")  # optional
MODERATOR_BOT_TOKEN = os.getenv("MODERATOR_BOT_TOKEN", "")  # moderator bot token
MODERATOR_CHAT_ID = int(os.getenv("MODERATOR_CHAT_ID", "0"))  # numeric Telegram user id of moderator

# Channels mapping (int -> friendly name)
CHANNELS: Dict[int, str] = {}

# Limits & cleanup policies
MAX_DRAFTS_IN_QUEUE = int(os.getenv("MAX_DRAFTS_IN_QUEUE", "10"))
REJECTED_POSTS_LIFETIME_HOURS = int(os.getenv("REJECTED_POSTS_LIFETIME_HOURS", "24"))
DRAFT_POSTS_LIFETIME_DAYS = int(os.getenv("DRAFT_POSTS_LIFETIME_DAYS", "2"))
AUTO_DELETE_ENABLED = os.getenv("AUTO_DELETE_ENABLED", "1") == "1"

# Paths
DB_PATH = os.getenv("DB_PATH", "./data/posts.db")
IMAGE_BANK_DIR = os.getenv("IMAGE_BANK_DIR", "./data/image_bank/")
GENERATED_IMAGES_DIR = os.getenv("GENERATED_IMAGES_DIR", "./data/images/")
BRAND_TEMPLATE_PATH = os.getenv("BRAND_TEMPLATE_PATH", "./app/assets/brand_template.png")

# Scheduler
SCHEDULER_INTERVAL_MIN = int(os.getenv("SCHEDULER_INTERVAL_MIN", "60"))  # minutes

# Categories
AVAILABLE_CATEGORIES = os.getenv("AVAILABLE_CATEGORIES", "finance,technology,health").split(",")
DEFAULT_CATEGORY = os.getenv("DEFAULT_CATEGORY", AVAILABLE_CATEGORIES[0] if AVAILABLE_CATEGORIES else "general")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Rclone remote
RCLONE_REMOTE = os.getenv("RCLONE_REMOTE", "remote:tg_backups")
