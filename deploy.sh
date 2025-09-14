#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$HOME/telegram_ai_channel_repo"
USER="$(whoami)"

if [ ! -d "${PROJECT_DIR}" ]; then
  git clone https://your.repo.url "${PROJECT_DIR}"
fi

cd "${PROJECT_DIR}"

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p data backups data/image_bank data/images app/assets

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Edit .env before running the service."
fi

python3 - <<PY
from app.db import ensure_schema
ensure_schema()
print("DB initialized")
PY

SERVICE="/etc/systemd/system/telegram_ai_scheduler.service"
sudo tee "${SERVICE}" >/dev/null <<EOF
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
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now telegram_ai_scheduler.service

echo "Deployed. Start moderator bot separately: venv/bin/python -m app.moderator_bot"
