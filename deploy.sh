#!/usr/bin/env bash
# deploy.sh - example deployment steps for Ubuntu/Debian VPS
set -euo pipefail

PROJECT_DIR="$HOME/telegram_ai_channel_repo"
USER="$(whoami)"

# Clone repo if not exists
if [ ! -d "${PROJECT_DIR}" ]; then
  git clone https://your.git.repo.url "${PROJECT_DIR}"
fi

cd "${PROJECT_DIR}"

# Create virtualenv & install deps
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create data directories
mkdir -p data backups data/image_bank data/images app/assets

# Create .env from example if doesn't exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Please edit .env and fill in API keys before starting the service."
fi

# Initialize DB schema
python3 - <<PY
from app.db import ensure_schema
ensure_schema()
print("DB initialized")
PY

# Install systemd service (adjust paths/user if needed)
SERVICE_FILE="/etc/systemd/system/telegram_ai_scheduler.service"
sudo tee "${SERVICE_FILE}" >/dev/null <<SERVICE
[Unit]
Description=Telegram AI Channel Scheduler and Moderator
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
echo "You should run moderator bot separately (systemd or as a service):"
echo "  ${PROJECT_DIR}/venv/bin/python -m app.moderator_bot"
