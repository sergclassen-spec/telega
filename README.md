# telega
app/
├── config.py # Centralized configuration
├── db.py # DB helpers and schema
├── utils.py # Common utilities (OpenAI, Telegram, images)
├── rss_fetcher.py # RSS ingestion
├── generator.py # Generation pipeline with moderation queue check
├── poster.py # Posting to Telegram (publisher bot)
├── moderator_bot.py # Integrated moderation bot (uses python-telegram-bot v20+)
├── scheduler.py # Scheduler: jobs + cleanup
└── tracker.py # Click tracker (unchanged)
backup.sh
requirements.txt
deploy.sh
