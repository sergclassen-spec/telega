# Technical Documentation: Telegram AI Channel System

## Overview

This is an automated Telegram channel management system that uses AI to generate engaging content from RSS feeds. The system fetches news from various RSS sources, processes them through OpenAI's GPT models to create provocative Telegram posts, and manages a moderation workflow before publishing.

## System Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RSS Fetcher   │───▶│   Generator     │───▶│  Moderation     │
│                 │    │   (OpenAI)      │    │     Bot         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   SQLite DB     │    │   Publisher     │
                       │   (Posts)       │    │     Bot         │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Scheduler     │    │   Telegram      │
                       │   (Cleanup)     │    │   Channels      │
                       └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **RSS Ingestion**: `rss_fetcher.py` periodically fetches news from configured RSS feeds
2. **Content Generation**: `generator.py` uses OpenAI to create provocative Telegram posts
3. **Moderation Queue**: Generated posts are stored in database with "on_moderation" status
4. **Human Review**: `moderator_bot.py` provides Telegram interface for content approval
5. **Publishing**: `poster.py` publishes approved content to Telegram channels
6. **Cleanup**: `scheduler.py` removes old rejected posts and manages lifecycle

## Detailed Component Analysis

### 1. Configuration Management (`config.py`)

**Purpose**: Centralized configuration using environment variables

**Key Features**:
- OpenAI API configuration (API key, model selection)
- Telegram bot tokens and channel IDs
- Database and file paths
- Content moderation settings
- Scheduler intervals

**Environment Variables**:
```bash
# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small

# Telegram
PUBLISHER_BOT_TOKEN=bot_token_for_publishing
PUBLISHER_CHANNEL_ID=-1001234567890
MODERATOR_BOT_TOKEN=bot_token_for_moderation
MODERATOR_CHAT_ID=123456789

# Database
DB_PATH=./data/posts.db
MAX_DRAFTS_IN_QUEUE=10
```

**Issues Identified**:
- `TRACKER_PORT` is referenced in `tracker.py` but not defined in config
- Missing error handling for invalid environment variables

### 2. Database Layer (`db.py`)

**Purpose**: SQLite database operations with WAL mode for concurrent access

**Schema**:
```sql
-- Posts table
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_title TEXT,
    source_url TEXT,
    raw_rss TEXT,
    text TEXT,
    image_path TEXT,
    status TEXT,  -- 'on_moderation', 'approved', 'rejected', 'published'
    channel_id INTEGER,
    category TEXT,
    tags TEXT,
    embedding TEXT,  -- JSON array for semantic similarity
    created_at INTEGER,
    updated_at INTEGER
);

-- Affiliate tracking
CREATE TABLE affiliates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_url TEXT,
    notes TEXT
);

-- Click tracking
CREATE TABLE clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    affiliate_id INTEGER,
    post_id INTEGER,
    ts INTEGER,
    ip TEXT,
    ua TEXT
);
```

**Key Functions**:
- `ensure_schema()`: Creates tables with proper indexes
- `count_posts_with_status()`: Queue management
- `get_old_rejected_and_stale()`: Cleanup operations

**Design Patterns**:
- Connection factory pattern
- WAL mode for better concurrency
- Row factory for dictionary-like access

### 3. RSS Feed Processing (`rss_fetcher.py`)

**Purpose**: Fetches and parses RSS feeds from multiple sources

**Current Feeds**:
- Reuters Business News
- Investing.com News

**Features**:
- Configurable limit per feed (default: 5 items)
- Error handling for malformed feeds
- Data normalization for consistent processing

**Limitations**:
- Hardcoded feed URLs
- No feed validation or health checking
- No retry mechanism for failed fetches

### 4. AI Content Generation (`generator.py`)

**Purpose**: Uses OpenAI to generate engaging Telegram posts from RSS content

**Generation Process**:
1. Checks moderation queue capacity
2. Creates provocative prompt for OpenAI
3. Generates text with specific constraints (≤280 chars, Russian language)
4. Creates embedding for semantic deduplication
5. Stores in database with "on_moderation" status

**Prompt Engineering**:
```
Generate a provocative Telegram post in Russian (<=280 chars) from this news.
Title: {title}
Summary: {summary}

- Make it intriguing and slightly controversial
- End with an open question
- Add 1-2 emojis and 2 relevant hashtags
```

**Deduplication**:
- Uses cosine similarity on embeddings (threshold: 0.78)
- Compares against all existing posts
- Prevents semantic duplicates

**Rate Limiting**:
- 1-second delay between generations
- Queue capacity limits (configurable)

### 5. Moderation System (`moderator_bot.py`)

**Purpose**: Telegram bot interface for content moderation

**Bot Commands**:
- `/start`: Authentication check
- `/moderate`: Show next post for review
- `/rejected`: List recent rejected posts
- `/stats`: Show moderation statistics

**Interactive Features**:
- ✅ Approve posts
- ❌ Reject posts
- ✏️ AI-powered text improvement
- 🎲 Random image assignment
- 🏷️ Category management

**Security**:
- User ID-based access control
- Command validation
- Error handling for malformed requests

**UI Components**:
- Inline keyboards for actions
- Photo support for image posts
- Real-time status updates

### 6. Publishing System (`poster.py`)

**Purpose**: Publishes approved content to Telegram channels

**Features**:
- Support for both text and photo posts
- Test channel publishing
- Status tracking (updates to "published")
- Error handling and logging

**Publishing Flow**:
1. Fetch next approved post
2. Determine target channel
3. Send via Telegram Bot API
4. Update database status
5. Log results

### 7. Scheduler (`scheduler.py`)

**Purpose**: Automated task scheduling and cleanup

**Scheduled Jobs**:
- **Content Generation**: Fetches RSS and generates posts (configurable interval)
- **Cleanup**: Removes old rejected posts (every 6 hours)

**Cleanup Policies**:
- Rejected posts: 24 hours (configurable)
- Stale moderation posts: 2 days (configurable)
- Image file cleanup
- Database record removal

**Scheduler Configuration**:
- Uses APScheduler with background execution
- Configurable intervals via environment variables
- Graceful shutdown handling

### 8. Click Tracking (`tracker.py`)

**Purpose**: Web service for affiliate link tracking

**Features**:
- Flask-based web service
- Affiliate link redirection
- Click analytics (IP, User-Agent, timestamp)
- Database logging

**Endpoints**:
- `GET /r/<affiliate_id>`: Redirects to target URL and logs click

**Issues**:
- Missing `TRACKER_PORT` configuration
- No authentication or rate limiting
- Basic error handling

### 9. Utility Functions (`utils.py`)

**Purpose**: Common utilities and external API integrations

**OpenAI Integration**:
- REST API calls (not SDK)
- Retry logic with exponential backoff
- Error handling and logging

**Telegram Integration**:
- Bot API calls for messaging
- Photo upload support
- Error handling

**Image Processing**:
- Random image selection from bank
- Brand template overlay
- PIL-based image manipulation

## External Dependencies

### Python Packages
```
requests>=2.31          # HTTP client
feedparser>=6.0         # RSS parsing
numpy>=1.23            # Vector operations for embeddings
Pillow>=9.0            # Image processing
APScheduler>=3.10      # Task scheduling
python-dotenv>=1.0     # Environment management
Flask>=2.2             # Web framework
python-telegram-bot>=20.7  # Telegram bot framework
gunicorn>=20.1         # WSGI server
loguru>=0.7            # Logging
```

### External Services
- **OpenAI API**: Content generation and embeddings
- **Telegram Bot API**: Message publishing and moderation interface
- **RSS Feeds**: Content sources (Reuters, Investing.com)

## Security Considerations

### Current Security Measures
- User ID-based access control for moderation bot
- Environment variable configuration
- SQLite WAL mode for data integrity
- Input validation in moderation interface

### Security Gaps
- No authentication for click tracker
- No rate limiting on external APIs
- No input sanitization for RSS content
- Missing HTTPS enforcement
- No audit logging for sensitive operations

## Performance Characteristics

### Scalability
- **Database**: SQLite with WAL mode supports moderate concurrency
- **API Rate Limits**: OpenAI and Telegram have rate limits
- **Memory Usage**: Minimal - primarily text processing
- **Storage**: Images stored locally, no CDN

### Bottlenecks
- OpenAI API response times
- Sequential RSS processing
- Single-threaded scheduler
- Local file storage for images

## Deployment Architecture

### System Requirements
- Python 3.8+
- SQLite3
- 1GB+ RAM
- 10GB+ storage
- Network access to OpenAI and Telegram APIs

### Deployment Process
1. **Environment Setup**: Clone repository, create virtual environment
2. **Dependencies**: Install requirements.txt
3. **Configuration**: Set up .env file with API keys
4. **Database**: Initialize schema
5. **Services**: Deploy as systemd services
6. **Monitoring**: Basic logging via loguru

### Service Configuration
```ini
[Unit]
Description=Telegram AI Scheduler
After=network.target

[Service]
User=telegram_user
WorkingDirectory=/path/to/project
EnvironmentFile=/path/to/.env
ExecStart=/path/to/venv/bin/python -m app.scheduler
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Monitoring and Maintenance

### Logging
- Uses loguru for structured logging
- Configurable log levels
- Error tracking and debugging information

### Backup Strategy
- Database backup via rclone to cloud storage
- Automated cleanup of old backups (30 days)
- SQLite backup with integrity checks

### Health Checks
- Scheduler job execution monitoring
- Database connectivity checks
- API endpoint availability

## Known Issues and Limitations

### Critical Issues
1. **Missing Configuration**: `TRACKER_PORT` not defined in config.py
2. **Error Handling**: Limited error recovery in several components
3. **Security**: No authentication for click tracker

### Functional Limitations
1. **Hardcoded Feeds**: RSS sources not configurable
2. **Single Language**: Only Russian language support
3. **No Analytics**: Limited metrics and reporting
4. **Manual Deployment**: No automated CI/CD pipeline

### Technical Debt
1. **Code Duplication**: Similar error handling patterns repeated
2. **Magic Numbers**: Hardcoded thresholds and limits
3. **Limited Testing**: No unit or integration tests
4. **Documentation**: Minimal inline documentation

## Recommendations for Improvement

### Immediate Fixes
1. Add `TRACKER_PORT` to config.py
2. Implement proper error handling
3. Add input validation and sanitization
4. Create comprehensive logging strategy

### Short-term Enhancements
1. Make RSS feeds configurable
2. Add multi-language support
3. Implement proper authentication
4. Add health check endpoints

### Long-term Improvements
1. Migrate to PostgreSQL for better scalability
2. Implement microservices architecture
3. Add comprehensive monitoring and alerting
4. Create automated testing suite
5. Implement CI/CD pipeline

## Conclusion

This system provides a solid foundation for automated Telegram channel management with AI-generated content. The architecture is well-structured with clear separation of concerns, but requires attention to security, error handling, and configuration management. The modular design allows for easy extension and modification of individual components.

The system is suitable for small to medium-scale operations but would need significant enhancements for enterprise-level deployment, particularly around security, monitoring, and scalability.