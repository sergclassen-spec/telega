# Deployment Guide

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.8 or higher
- **Memory**: 1GB+ RAM
- **Storage**: 10GB+ available space
- **Network**: Internet access for APIs

### Required Accounts
- **OpenAI Account**: For content generation API
- **Telegram Bot**: Create via @BotFather
- **Cloud Storage** (optional): For backups (rclone compatible)

## Installation Steps

### 1. System Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv sqlite3 git -y

# Create application user
sudo useradd -m -s /bin/bash telegram_user
sudo usermod -aG sudo telegram_user
```

### 2. Repository Setup

```bash
# Switch to application user
sudo su - telegram_user

# Clone repository
git clone https://your-repo-url.git /home/telegram_user/telegram_ai_channel
cd /home/telegram_user/telegram_ai_channel

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Create environment file
cp .env.example .env
nano .env
```

**Required Environment Variables**:
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small

# Telegram Configuration
PUBLISHER_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
PUBLISHER_CHANNEL_ID=-1001234567890
TEST_CHANNEL_ID=-1001234567891
MODERATOR_BOT_TOKEN=1234567890:XYZabcDEFghiJKLmnoPQRstuv
MODERATOR_CHAT_ID=123456789

# Database Configuration
DB_PATH=./data/posts.db
MAX_DRAFTS_IN_QUEUE=10
REJECTED_POSTS_LIFETIME_HOURS=24
DRAFT_POSTS_LIFETIME_DAYS=2
AUTO_DELETE_ENABLED=1

# File Paths
IMAGE_BANK_DIR=./data/image_bank/
GENERATED_IMAGES_DIR=./data/images/
BRAND_TEMPLATE_PATH=./app/assets/brand_template.png

# Scheduler Configuration
SCHEDULER_INTERVAL_MIN=60

# Categories
AVAILABLE_CATEGORIES=finance,technology,health
DEFAULT_CATEGORY=finance

# Logging
LOG_LEVEL=INFO

# Backup Configuration
RCLONE_REMOTE=remote:tg_backups

# Click Tracker (add this missing configuration)
TRACKER_PORT=8080
```

### 4. Directory Structure Setup

```bash
# Create necessary directories
mkdir -p data backups data/image_bank data/images app/assets

# Set proper permissions
chmod 755 data backups data/image_bank data/images app/assets
```

### 5. Database Initialization

```bash
# Initialize database schema
python3 -c "from app.db import ensure_schema; ensure_schema(); print('Database initialized')"
```

### 6. Bot Setup

#### Publisher Bot Setup
1. Create bot via @BotFather on Telegram
2. Get bot token and add to `PUBLISHER_BOT_TOKEN`
3. Add bot to your channel as administrator
4. Get channel ID and add to `PUBLISHER_CHANNEL_ID`

#### Moderator Bot Setup
1. Create another bot via @BotFather
2. Get bot token and add to `MODERATOR_BOT_TOKEN`
3. Start conversation with bot
4. Get your user ID and add to `MODERATOR_CHAT_ID`

**Getting Channel ID**:
```bash
# Add bot to channel, then send a message
# Check logs or use Telegram API to get channel ID
curl "https://api.telegram.org/bot<BOT_TOKEN>/getUpdates"
```

**Getting User ID**:
```bash
# Send /start to bot, then check updates
curl "https://api.telegram.org/bot<BOT_TOKEN>/getUpdates"
```

### 7. Systemd Service Setup

#### Scheduler Service
```bash
sudo tee /etc/systemd/system/telegram_ai_scheduler.service > /dev/null <<EOF
[Unit]
Description=Telegram AI Scheduler
After=network.target

[Service]
User=telegram_user
WorkingDirectory=/home/telegram_user/telegram_ai_channel
EnvironmentFile=/home/telegram_user/telegram_ai_channel/.env
ExecStart=/home/telegram_user/telegram_ai_channel/venv/bin/python -m app.scheduler
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

#### Moderator Bot Service
```bash
sudo tee /etc/systemd/system/telegram_ai_moderator.service > /dev/null <<EOF
[Unit]
Description=Telegram AI Moderator Bot
After=network.target

[Service]
User=telegram_user
WorkingDirectory=/home/telegram_user/telegram_ai_channel
EnvironmentFile=/home/telegram_user/telegram_ai_channel/.env
ExecStart=/home/telegram_user/telegram_ai_channel/venv/bin/python -m app.moderator_bot
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

#### Click Tracker Service
```bash
sudo tee /etc/systemd/system/telegram_ai_tracker.service > /dev/null <<EOF
[Unit]
Description=Telegram AI Click Tracker
After=network.target

[Service]
User=telegram_user
WorkingDirectory=/home/telegram_user/telegram_ai_channel
EnvironmentFile=/home/telegram_user/telegram_ai_channel/.env
ExecStart=/home/telegram_user/telegram_ai_channel/venv/bin/python -m app.tracker
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### 8. Service Management

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable telegram_ai_scheduler.service
sudo systemctl enable telegram_ai_moderator.service
sudo systemctl enable telegram_ai_tracker.service

# Start services
sudo systemctl start telegram_ai_scheduler.service
sudo systemctl start telegram_ai_moderator.service
sudo systemctl start telegram_ai_tracker.service

# Check status
sudo systemctl status telegram_ai_scheduler.service
sudo systemctl status telegram_ai_moderator.service
sudo systemctl status telegram_ai_tracker.service
```

## Verification

### 1. Check Service Status
```bash
# All services should be active
sudo systemctl status telegram_ai_*.service

# Check logs
sudo journalctl -u telegram_ai_scheduler.service -f
sudo journalctl -u telegram_ai_moderator.service -f
sudo journalctl -u telegram_ai_tracker.service -f
```

### 2. Test Database
```bash
# Check database exists and has tables
sqlite3 data/posts.db ".tables"
sqlite3 data/posts.db "SELECT COUNT(*) FROM posts;"
```

### 3. Test Moderation Bot
1. Send `/start` to moderator bot
2. Should receive "Moderator bot ready. Use /moderate"
3. Send `/moderate` to check for posts

### 4. Test Click Tracker
```bash
# Test redirect endpoint
curl -I http://localhost:8080/r/1
```

## Backup Configuration

### 1. Install rclone (optional)
```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure remote storage
rclone config
```

### 2. Setup Backup Cron Job
```bash
# Add to crontab
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /home/telegram_user/telegram_ai_channel/backup.sh
```

## Monitoring

### 1. Log Monitoring
```bash
# Follow all service logs
sudo journalctl -u telegram_ai_*.service -f

# Check specific service
sudo journalctl -u telegram_ai_scheduler.service --since "1 hour ago"
```

### 2. Database Monitoring
```bash
# Check post counts by status
sqlite3 data/posts.db "SELECT status, COUNT(*) FROM posts GROUP BY status;"

# Check recent activity
sqlite3 data/posts.db "SELECT id, status, created_at FROM posts ORDER BY created_at DESC LIMIT 10;"
```

### 3. System Monitoring
```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check process status
ps aux | grep python
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check service status
sudo systemctl status telegram_ai_scheduler.service

# Check logs for errors
sudo journalctl -u telegram_ai_scheduler.service -n 50

# Check environment file
sudo -u telegram_user cat /home/telegram_user/telegram_ai_channel/.env
```

#### 2. Database Issues
```bash
# Check database file permissions
ls -la data/posts.db

# Check database integrity
sqlite3 data/posts.db "PRAGMA integrity_check;"

# Recreate database if corrupted
rm data/posts.db
python3 -c "from app.db import ensure_schema; ensure_schema()"
```

#### 3. API Issues
```bash
# Test OpenAI API
python3 -c "
from app.utils import openai_chat
result = openai_chat('Test message')
print('OpenAI API:', 'OK' if result else 'FAILED')
"

# Test Telegram API
python3 -c "
from app.utils import post_message_to_channel
from app.config import PUBLISHER_BOT_TOKEN, TEST_CHANNEL_ID
try:
    post_message_to_channel(PUBLISHER_BOT_TOKEN, TEST_CHANNEL_ID, 'Test message')
    print('Telegram API: OK')
except Exception as e:
    print('Telegram API: FAILED -', e)
"
```

#### 4. Permission Issues
```bash
# Fix ownership
sudo chown -R telegram_user:telegram_user /home/telegram_user/telegram_ai_channel

# Fix permissions
chmod 755 /home/telegram_user/telegram_ai_channel
chmod 644 /home/telegram_user/telegram_ai_channel/.env
```

### Performance Tuning

#### 1. Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_posts_status_created ON posts(status, created_at);
CREATE INDEX IF NOT EXISTS idx_posts_embedding ON posts(embedding);
```

#### 2. Memory Optimization
```bash
# Monitor memory usage
htop

# Adjust Python memory settings if needed
export PYTHONHASHSEED=0
export PYTHONUNBUFFERED=1
```

#### 3. Network Optimization
```bash
# Test network connectivity
ping api.openai.com
ping api.telegram.org

# Check DNS resolution
nslookup api.openai.com
nslookup api.telegram.org
```

## Security Hardening

### 1. File Permissions
```bash
# Secure environment file
chmod 600 .env

# Secure database
chmod 600 data/posts.db

# Secure directories
chmod 700 data backups
```

### 2. Firewall Configuration
```bash
# Install ufw
sudo apt install ufw -y

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8080/tcp  # Click tracker port
sudo ufw enable
```

### 3. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
pip list --outdated
pip install --upgrade package_name
```

## Maintenance

### 1. Regular Tasks
- Monitor disk space usage
- Check service status daily
- Review logs for errors
- Backup database regularly
- Update dependencies monthly

### 2. Database Maintenance
```bash
# Vacuum database monthly
sqlite3 data/posts.db "VACUUM;"

# Analyze database
sqlite3 data/posts.db "ANALYZE;"
```

### 3. Log Rotation
```bash
# Configure logrotate
sudo tee /etc/logrotate.d/telegram_ai > /dev/null <<EOF
/var/log/telegram_ai/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 telegram_user telegram_user
}
EOF
```

This deployment guide provides comprehensive instructions for setting up the Telegram AI Channel system in a production environment with proper security, monitoring, and maintenance procedures.