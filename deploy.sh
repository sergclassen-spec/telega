#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$HOME/telegram_ai_channel_repo"
USER="$(whoami)"

if [ ! -d "${PROJECT_DIR}" ]; then
  git clone https://your.git.repo.url "${PROJECT_DIR}"
fi

cd "${PROJECT_DIR}"

# virtualenv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# dirs
mkdir -p data backups data/image_bank data/images app/assets

# copy .env.example if .env missing
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Please edit .env with real API keys and channel IDs."
fi

# initialize DB
python3 - <<PY
from app.db import ensure_schema
ensure_schema()
print("DB initialized")
PY

# systemd service for scheduler
SERVICE_FILE="/etc/systemd/system/telegram_ai_scheduler.service"
sudo tee "${SERVICE_FILE}" >/dev/null <<SERVICE
[Unit]
Description=Telegram AI Scheduler
After=network.target

[Service]
User=${USER}
WorkingDirectory=${PROJECT_DIR}
EnvironmentFile=${PROJECT_DIR}/.env
ExecStart=${PROJECT_DIR}/venv/bin/python -m app.scheduler
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable telegram_ai_scheduler.service
sudo systemctl start telegram_ai_scheduler.service

echo "Scheduler service installed and started."
echo "Start moderator bot separately: ${PROJECT_DIR}/venv/bin/python -m app.moderator_bot"
